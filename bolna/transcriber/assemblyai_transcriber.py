import asyncio
import traceback
import os
import json
import aiohttp
import time
import websockets
from urllib.parse import urlencode
from dotenv import load_dotenv
from websockets.asyncio.client import ClientConnection
from websockets.exceptions import ConnectionClosedError, InvalidHandshake

from .base_transcriber import BaseTranscriber
from bolna.helpers.logger_config import configure_logger
from bolna.helpers.utils import create_ws_data_packet

logger = configure_logger(__name__)
load_dotenv()


class AssemblyAITranscriber(BaseTranscriber):
    def __init__(self, telephony_provider, input_queue=None, model='best', stream=True, language="en", 
                 sampling_rate="16000", encoding="linear16", output_queue=None, keywords=None, **kwargs):
        super().__init__(input_queue)
        self.language = language
        self.stream = stream
        self.provider = telephony_provider
        self.heartbeat_task = None
        self.sender_task = None
        self.model = model
        self.sampling_rate = int(sampling_rate)
        self.encoding = encoding
        self.api_key = kwargs.get("transcriber_key", os.getenv('ASSEMBLYAI_API_KEY'))
        self.assemblyai_host = os.getenv('ASSEMBLYAI_HOST', 'api.assemblyai.com')
        self.transcriber_output_queue = output_queue
        self.transcription_task = None
        self.keywords = keywords
        self.audio_cursor = 0.0
        self.transcription_cursor = 0.0
        self.interruption_signalled = False
        self.audio_submitted = False
        self.audio_submission_time = None
        self.num_frames = 0
        self.connection_start_time = None
        self.audio_frame_duration = 0.0
        self.connected_via_dashboard = kwargs.get("enforce_streaming", True)
        
        # Message states
        self.curr_message = ''
        self.finalized_transcript = ""
        self.final_transcript = ""
        self.is_transcript_sent_for_processing = False
        self.websocket_connection = None
        self.connection_authenticated = False

    def get_assemblyai_ws_url(self):
        """Generate Assembly AI WebSocket URL with proper parameters"""
        aa_params = {
            'sample_rate': self.sampling_rate,
            'encoding': self.encoding,
            'language_code': self.language,
            'word_boost': self.keywords if self.keywords else '',
            'boost_param': 'high',
            'punctuate': 'true',
            'format_text': 'true',
            'utterance_end_ms': '1000',
            'end_utterance_silence_threshold': '500'
        }

        # Set audio frame duration based on provider
        if self.provider in ('twilio', 'exotel', 'plivo'):
            self.encoding = 'mulaw' if self.provider in ("twilio") else "linear16"
            self.sampling_rate = 8000
            self.audio_frame_duration = 0.2  # 200ms frames for telephony
            aa_params['sample_rate'] = self.sampling_rate
            aa_params['encoding'] = self.encoding
        elif self.provider == "web_based_call":
            aa_params['sample_rate'] = 16000
            aa_params['encoding'] = "linear16"
            self.sampling_rate = 16000
            self.audio_frame_duration = 0.256
        else:
            aa_params['sample_rate'] = 16000
            aa_params['encoding'] = "linear16"
            self.sampling_rate = 16000
            self.audio_frame_duration = 0.5

        # Remove empty parameters
        aa_params = {k: v for k, v in aa_params.items() if v}

        websocket_api = f'wss://{self.assemblyai_host}/v2/realtime/ws'
        websocket_url = websocket_api + '?' + urlencode(aa_params)
        return websocket_url

    async def send_heartbeat(self, ws: ClientConnection):
        """Send periodic heartbeat to keep connection alive"""
        try:
            while True:
                data = {'type': 'ping'}
                try:
                    await ws.send(json.dumps(data))
                except ConnectionClosedError as e:
                    logger.info(f"Connection closed while sending heartbeat: {e}")
                    break
                except Exception as e:
                    logger.error(f"Error sending heartbeat: {e}")
                    break
                    
                await asyncio.sleep(5)  # Send heartbeat every 5 seconds
        except asyncio.CancelledError:
            logger.info("Heartbeat task cancelled")
            raise
        except Exception as e:
            logger.error('Error in send_heartbeat: ' + str(e))
            raise

    async def toggle_connection(self):
        """Close the connection and clean up tasks"""
        self.connection_on = False
        if self.heartbeat_task is not None:
            self.heartbeat_task.cancel()
        if self.sender_task is not None:
            self.sender_task.cancel()
        
        if self.websocket_connection is not None:
            try:
                await self.websocket_connection.close()
                logger.info("WebSocket connection closed successfully")
            except Exception as e:
                logger.error(f"Error closing websocket connection: {e}")
            finally:
                self.websocket_connection = None
                self.connection_authenticated = False

    async def _check_and_process_end_of_stream(self, ws_data_packet, ws):
        """Check if this is the end of stream and handle accordingly"""
        if 'eos' in ws_data_packet['meta_info'] and ws_data_packet['meta_info']['eos'] is True:
            await self._close(ws, data={"type": "CloseStream"})
            return True
        return False

    def get_meta_info(self):
        return self.meta_info

    async def sender_stream(self, ws: ClientConnection):
        """Send audio data to Assembly AI WebSocket"""
        try:
            while True:
                ws_data_packet = await self.input_queue.get()
                
                if not self.audio_submitted:
                    self.meta_info = ws_data_packet.get('meta_info')
                    self.audio_submitted = True
                    self.audio_submission_time = time.time()
                    self.current_request_id = self.generate_request_id()
                    self.meta_info['request_id'] = self.current_request_id

                end_of_stream = await self._check_and_process_end_of_stream(ws_data_packet, ws)
                if end_of_stream:
                    break
                    
                self.num_frames += 1
                self.audio_cursor = self.num_frames * self.audio_frame_duration
                
                try:
                    await ws.send(ws_data_packet.get('data'))
                except ConnectionClosedError as e:
                    logger.error(f"Connection closed while sending data: {e}")
                    break
                except Exception as e:
                    logger.error(f"Error sending data to websocket: {e}")
                    break
                    
        except asyncio.CancelledError:
            logger.info("Sender stream task cancelled")
            raise
        except Exception as e:
            logger.error('Error in sender_stream: ' + str(e))
            raise

    async def receiver(self, ws: ClientConnection):
        """Receive transcription results from Assembly AI WebSocket"""
        async for msg in ws:
            try:
                msg = json.loads(msg)

                if self.connection_start_time is None:
                    self.connection_start_time = (time.time() - (self.num_frames * self.audio_frame_duration))

                if msg.get("message_type") == "SessionBegins":
                    logger.info("Assembly AI session started")
                    yield create_ws_data_packet("speech_started", self.meta_info)

                elif msg.get("message_type") == "PartialTranscript":
                    transcript = msg.get("text", "")
                    if transcript.strip():
                        data = {
                            "type": "interim_transcript_received",
                            "content": transcript
                        }
                        yield create_ws_data_packet(data, self.meta_info)

                elif msg.get("message_type") == "FinalTranscript":
                    transcript = msg.get("text", "")
                    if transcript.strip():
                        logger.info(f"Received final transcript: {transcript}")
                        data = {
                            "type": "transcript",
                            "content": transcript
                        }
                        yield create_ws_data_packet(data, self.meta_info)

                elif msg.get("message_type") == "SessionTerminated":
                    logger.info("Assembly AI session terminated")
                    yield create_ws_data_packet("transcriber_connection_closed", self.meta_info)
                    return

            except Exception as e:
                traceback.print_exc()
                logger.error(f"Error processing message: {e}")

    async def push_to_transcriber_queue(self, data_packet):
        """Push transcription result to output queue"""
        await self.transcriber_output_queue.put(data_packet)

    async def assemblyai_connect(self):
        """Establish WebSocket connection to Assembly AI"""
        try:
            websocket_url = self.get_assemblyai_ws_url()
            additional_headers = {
                'Authorization': self.api_key
            }
            
            logger.info(f"Attempting to connect to Assembly AI WebSocket: {websocket_url}")
            
            assemblyai_ws = await asyncio.wait_for(
                websockets.connect(websocket_url, additional_headers=additional_headers),
                timeout=10.0
            )
            
            self.websocket_connection = assemblyai_ws
            self.connection_authenticated = True
            logger.info("Successfully connected to Assembly AI WebSocket")
            
            return assemblyai_ws
            
        except asyncio.TimeoutError:
            logger.error("Timeout while connecting to Assembly AI WebSocket")
            raise ConnectionError("Timeout while connecting to Assembly AI WebSocket")
        except InvalidHandshake as e:
            logger.error(f"Invalid handshake during Assembly AI WebSocket connection: {e}")
            raise ConnectionError(f"Invalid handshake during Assembly AI WebSocket connection: {e}")
        except ConnectionClosedError as e:
            logger.error(f"Assembly AI WebSocket connection closed unexpectedly: {e}")
            raise ConnectionError(f"Assembly AI WebSocket connection closed unexpectedly: {e}")
        except Exception as e:
            logger.error(f"Unexpected error connecting to Assembly AI WebSocket: {e}")
            raise ConnectionError(f"Unexpected error connecting to Assembly AI WebSocket: {e}")

    async def run(self):
        """Start the transcription task"""
        try:
            self.transcription_task = asyncio.create_task(self.transcribe())
        except Exception as e:
            logger.error(f"Error starting transcription task: {e}")

    async def transcribe(self):
        """Main transcription loop"""
        assemblyai_ws = None
        try:
            start_time = time.perf_counter()
            
            try:
                assemblyai_ws = await self.assemblyai_connect()
            except (ValueError, ConnectionError) as e:
                logger.error(f"Failed to establish Assembly AI connection: {e}")
                await self.toggle_connection()
                return
            
            if not self.connection_time:
                self.connection_time = round((time.perf_counter() - start_time) * 1000)

            if self.stream:
                self.sender_task = asyncio.create_task(self.sender_stream(assemblyai_ws))
                self.heartbeat_task = asyncio.create_task(self.send_heartbeat(assemblyai_ws))
                
                try:
                    async for message in self.receiver(assemblyai_ws):
                        if self.connection_on:
                            await self.push_to_transcriber_queue(message)
                        else:
                            logger.info("Closing the Assembly AI connection")
                            await self._close(assemblyai_ws, data={"type": "CloseStream"})
                            break
                except ConnectionClosedError as e:
                    logger.error(f"Assembly AI WebSocket connection closed during streaming: {e}")
                except Exception as e:
                    logger.error(f"Error during streaming: {e}")
                    raise

        except (ValueError, ConnectionError) as e:
            logger.error(f"Connection error in transcribe: {e}")
            await self.toggle_connection()
        except Exception as e:
            logger.error(f"Unexpected error in transcribe: {e}")
            await self.toggle_connection()
        finally:
            if assemblyai_ws is not None:
                try:
                    await assemblyai_ws.close()
                    logger.info("Assembly AI WebSocket closed in finally block")
                except Exception as e:
                    logger.error(f"Error closing websocket in finally block: {e}")
                finally:
                    self.websocket_connection = None
                    self.connection_authenticated = False
            
            if hasattr(self, 'sender_task') and self.sender_task is not None:
                self.sender_task.cancel()
            if hasattr(self, 'heartbeat_task') and self.heartbeat_task is not None:
                self.heartbeat_task.cancel()
            
            await self.push_to_transcriber_queue(
                create_ws_data_packet("transcriber_connection_closed", getattr(self, 'meta_info', {}))
            )
