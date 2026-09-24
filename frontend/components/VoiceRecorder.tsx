'use client';

import { useEffect, useRef, useState } from 'react';
import { Mic, MicOff, Square, AlertTriangle, Upload, CheckCircle } from 'lucide-react';

interface VoiceRecorderProps {
  onTranscript: (text: string) => void;
  onAudioBlob?: (blob: Blob) => void;
  disabled?: boolean;
  language?: string; // 'en-IN' | 'hi-IN' | 'or-IN'
}

type RecordState = 'idle' | 'recording' | 'done' | 'unsupported';

const LANG_LABELS: Record<string, string> = {
  'en-IN': 'English',
  'hi-IN': 'हिन्दी',
  'or-IN': 'ଓଡ଼ିଆ',
  en: 'English',
  hi: 'हिन्दी',
  or: 'ଓଡ଼ିଆ',
};

export default function VoiceRecorder({
  onTranscript,
  onAudioBlob,
  disabled = false,
  language = 'en-IN',
}: VoiceRecorderProps) {
  const [state, setState] = useState<RecordState>('idle');
  const [liveText, setLiveText] = useState('');
  const [finalText, setFinalText] = useState('');
  const [error, setError] = useState('');
  const [mediaRecording, setMediaRecording] = useState(false);

  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Check browser support
  const hasSpeechAPI =
    typeof window !== 'undefined' &&
    ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window);

  useEffect(() => {
    if (!hasSpeechAPI) {
      setState('unsupported');
    }
    return () => {
      stopAll();
    };
  }, [hasSpeechAPI]);

  function stopAll() {
    recognitionRef.current?.stop();
    if (mediaRecorderRef.current?.state === 'recording') {
      mediaRecorderRef.current.stop();
    }
  }

  function startRecording() {
    if (disabled) return;
    setError('');
    setLiveText('');
    setFinalText('');
    setState('recording');

    const SpeechRecognitionAPI =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    const recognition: SpeechRecognition = new SpeechRecognitionAPI();
    recognition.lang = language;
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let interim = '';
      let final = finalText;
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          final += ' ' + transcript;
        } else {
          interim += transcript;
        }
      }
      setFinalText(final.trim());
      setLiveText(interim);
    };

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      const msg =
        event.error === 'not-allowed'
          ? 'Microphone access denied. Please allow microphone in browser settings.'
          : event.error === 'no-speech'
          ? 'No speech detected. Please speak clearly and try again.'
          : `Recognition error: ${event.error}`;
      setError(msg);
      setState('idle');
    };

    recognition.onend = () => {
      if (state === 'recording') {
        // auto-ended (silence timeout) — commit what we have
        commitTranscript();
      }
    };

    recognitionRef.current = recognition;
    recognition.start();

    // Also record audio for optional server-side upload
    if (onAudioBlob) {
      navigator.mediaDevices
        .getUserMedia({ audio: true })
        .then((stream) => {
          const mr = new MediaRecorder(stream);
          chunksRef.current = [];
          mr.ondataavailable = (e) => {
            if (e.data.size > 0) chunksRef.current.push(e.data);
          };
          mr.onstop = () => {
            const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
            onAudioBlob(blob);
            stream.getTracks().forEach((t) => t.stop());
          };
          mediaRecorderRef.current = mr;
          mr.start();
          setMediaRecording(true);
        })
        .catch(() => {
          // Audio blob recording failed but transcript still works
        });
    }
  }

  function stopRecording() {
    recognitionRef.current?.stop();
    mediaRecorderRef.current?.stop();
    setMediaRecording(false);
    commitTranscript();
  }

  function commitTranscript() {
    const text = (finalText + ' ' + liveText).trim();
    if (text) {
      onTranscript(text);
      setState('done');
    } else {
      setState('idle');
    }
  }

  function reset() {
    stopAll();
    setLiveText('');
    setFinalText('');
    setError('');
    setState('idle');
  }

  // File upload fallback for unsupported browsers
  function handleFileUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    if (onAudioBlob) onAudioBlob(file);
    setError('');
    setState('done');
    onTranscript(`[Audio file uploaded: ${file.name}. Transcript will be generated server-side.]`);
  }

  const combined = (finalText + ' ' + liveText).trim();

  if (state === 'unsupported') {
    return (
      <div className="rounded-lg border border-amber-200 bg-amber-50 p-4">
        <div className="flex items-start gap-2">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />
          <div>
            <p className="text-sm font-medium text-amber-800">
              Browser voice input not supported
            </p>
            <p className="mt-1 text-xs text-amber-700">
              Use Chrome, Edge, or Safari for voice input. Or upload an audio file below.
            </p>
          </div>
        </div>
        {onAudioBlob && (
          <div className="mt-3">
            <input
              ref={fileInputRef}
              type="file"
              accept="audio/*"
              className="hidden"
              onChange={handleFileUpload}
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              className="flex items-center gap-2 rounded-md border border-amber-400 bg-white px-3 py-2 text-sm text-amber-700 hover:bg-amber-50"
            >
              <Upload className="h-4 w-4" />
              Upload audio file (wav / mp3 / webm)
            </button>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Disclaimer */}
      <div className="flex items-start gap-2 rounded-md bg-blue-50 p-3 text-xs text-blue-700">
        <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
        <span>
          Voice is transcribed locally in your browser using the Web Speech API.
          Audio is <strong>NOT</strong> sent to any server unless you explicitly submit
          the form with server-side transcription enabled.
        </span>
      </div>

      {/* Controls */}
      <div className="flex items-center gap-3">
        {state === 'idle' && (
          <button
            onClick={startRecording}
            disabled={disabled}
            className="flex min-h-[44px] items-center gap-2 rounded-lg bg-red-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
          >
            <Mic className="h-4 w-4" />
            Start Recording
            {LANG_LABELS[language] && (
              <span className="ml-1 rounded bg-red-800 px-1.5 py-0.5 text-xs">
                {LANG_LABELS[language]}
              </span>
            )}
          </button>
        )}

        {state === 'recording' && (
          <>
            <button
              onClick={stopRecording}
              className="flex min-h-[44px] animate-pulse items-center gap-2 rounded-lg bg-red-700 px-5 py-2.5 text-sm font-medium text-white"
            >
              <Square className="h-4 w-4 fill-white" />
              Stop Recording
            </button>
            <div className="flex items-center gap-1.5 text-xs text-red-600">
              <span className="h-2.5 w-2.5 animate-ping rounded-full bg-red-500" />
              Recording…
            </div>
          </>
        )}

        {state === 'done' && (
          <>
            <div className="flex items-center gap-2 text-sm text-green-700">
              <CheckCircle className="h-4 w-4" />
              Transcript captured
            </div>
            <button
              onClick={reset}
              className="rounded-md border border-gray-300 px-3 py-1.5 text-xs text-gray-600 hover:bg-gray-50"
            >
              Re-record
            </button>
          </>
        )}
      </div>

      {/* Live transcript */}
      {state === 'recording' && (
        <div className="min-h-[80px] rounded-lg border border-red-200 bg-red-50 p-3 text-sm">
          <p className="mb-1 text-xs font-medium uppercase tracking-wide text-red-500">
            Live transcript
          </p>
          <p className="text-gray-800">
            {finalText && <span>{finalText} </span>}
            {liveText && (
              <span className="italic text-gray-400">{liveText}</span>
            )}
            {!combined && (
              <span className="italic text-gray-400">Speak now…</span>
            )}
          </p>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="flex items-start gap-2 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          <MicOff className="mt-0.5 h-4 w-4 shrink-0" />
          {error}
        </div>
      )}
    </div>
  );
}
