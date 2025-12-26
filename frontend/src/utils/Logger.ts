/**
 * Frontend logger that sends logs to backend.
 * Captures console output and batches network writes.
 */

interface LogEntry {
  Level: "debug" | "info" | "warn" | "error";
  Message: string;
  Context?: Record<string, any>;
  Timestamp: string;
}

type LogLevelName = "debug" | "info" | "warn" | "error" | "silent";

const LogLevelOrder: Record<LogLevelName, number> = {
  debug: 10,
  info: 20,
  warn: 30,
  error: 40,
  silent: 99
};

const OriginalConsole = {
  debug: console.debug.bind(console),
  info: console.info.bind(console),
  warn: console.warn.bind(console),
  error: console.error.bind(console),
  log: console.log.bind(console)
};

const IsTestEnv = import.meta.env?.VITEST === "true" || import.meta.env?.MODE === "test";

const NormalizeLogLevel = (Value: string | undefined): LogLevelName => {
  const Candidate = (Value || "info").toLowerCase();
  if (Candidate === "debug" || Candidate === "info" || Candidate === "warn" || Candidate === "error" || Candidate === "silent") {
    return Candidate;
  }
  return "info";
};

const ParseBoolean = (Value: string | undefined, DefaultValue: boolean): boolean => {
  if (Value === undefined) return DefaultValue;
  return Value.toLowerCase() === "true";
};

const ParseNumber = (Value: string | undefined, DefaultValue: number): number => {
  if (!Value) return DefaultValue;
  const Parsed = Number(Value);
  return Number.isFinite(Parsed) ? Parsed : DefaultValue;
};

const ResolveLogEndpoint = (): string => {
  const BaseUrl = import.meta.env.VITE_API_BASE_URL;
  if (BaseUrl && BaseUrl.startsWith("http")) {
    return new URL("/api/logs/batch", BaseUrl).toString();
  }
  return "/api/logs/batch";
};

const LogEndpoint = ResolveLogEndpoint();

const NormalizeContextValue = (Value: any): any => {
  if (Value instanceof Error) {
    return {
      Name: Value.name,
      Message: Value.message,
      Stack: Value.stack
    };
  }
  if (Value === undefined) {
    return "undefined";
  }
  if (typeof Value === "function") {
    return "[Function]";
  }
  if (typeof Value === "symbol") {
    return Value.toString();
  }
  if (typeof Value === "bigint") {
    return Value.toString();
  }
  if (Value === null || typeof Value === "string" || typeof Value === "number" || typeof Value === "boolean") {
    return Value;
  }
  try {
    JSON.stringify(Value);
    return Value;
  } catch {
    return String(Value);
  }
};

class Logger {
  private Queue: LogEntry[] = [];
  private SendInterval: number;
  private MaxBatchSize: number;
  private Timer: NodeJS.Timeout | null = null;
  private LogLevel: LogLevelName;
  private IsEnabled: boolean;
  private CaptureConsole: boolean;
  private IsConsoleCaptured: boolean = false;
  private IsInitialized: boolean = false;
  private HandleWindowError: ((Event: ErrorEvent) => void) | null = null;
  private HandleUnhandledRejection: ((Event: PromiseRejectionEvent) => void) | null = null;

  constructor() {
    this.LogLevel = NormalizeLogLevel(import.meta.env.VITE_LOG_LEVEL);
    this.SendInterval = ParseNumber(import.meta.env.VITE_LOG_BATCH_INTERVAL_MS, 5000);
    this.MaxBatchSize = ParseNumber(import.meta.env.VITE_LOG_BATCH_SIZE, 10);
    this.IsEnabled = !IsTestEnv && this.LogLevel !== "silent";
    this.CaptureConsole = this.IsEnabled && ParseBoolean(import.meta.env.VITE_LOG_CAPTURE_CONSOLE, true);
  }

  Initialize() {
    if (this.IsInitialized || !this.IsEnabled) return;
    this.IsInitialized = true;

    this.Timer = setInterval(() => this.Flush(), this.SendInterval);

    if (this.CaptureConsole && typeof window !== "undefined") {
      this.SetupConsoleCapture();
    }

    if (typeof window !== "undefined") {
      this.BindGlobalErrorHandlers();
      window.addEventListener("beforeunload", () => this.Flush());
    }
  }

  private EnsureInitialized() {
    if (!this.IsInitialized) {
      this.Initialize();
    }
  }

  private ShouldLog(Level: LogEntry["Level"]): boolean {
    return LogLevelOrder[Level] >= LogLevelOrder[this.LogLevel];
  }

  private SetupConsoleCapture() {
    if (this.IsConsoleCaptured) return;
    this.IsConsoleCaptured = true;

    console.debug = (...Args: any[]) => {
      OriginalConsole.debug(...Args);
      this.LogConsole("debug", Args);
    };
    console.info = (...Args: any[]) => {
      OriginalConsole.info(...Args);
      this.LogConsole("info", Args);
    };
    console.warn = (...Args: any[]) => {
      OriginalConsole.warn(...Args);
      this.LogConsole("warn", Args);
    };
    console.error = (...Args: any[]) => {
      OriginalConsole.error(...Args);
      this.LogConsole("error", Args);
    };
    console.log = (...Args: any[]) => {
      OriginalConsole.log(...Args);
      this.LogConsole("info", Args);
    };
  }

  private LogConsole(Level: LogEntry["Level"], Args: any[]) {
    const { Message, Context } = this.BuildMessageAndContext(Args);
    this.Enqueue(Level, Message, Context);
  }

  private BuildMessageAndContext(Args: any[]): { Message: string; Context?: Record<string, any> } {
    if (!Args.length) {
      return { Message: "Console log" };
    }

    const [First, ...Rest] = Args;
    const Message = typeof First === "string" ? First : String(First);
    const AllArgs = [First, ...Rest].map(NormalizeContextValue);

    if (AllArgs.length === 1 && typeof First === "string") {
      return { Message };
    }

    return {
      Message,
      Context: { Args: AllArgs }
    };
  }

  private Enqueue(Level: LogEntry["Level"], Message: string, Context?: Record<string, any>) {
    if (!this.ShouldLog(Level)) return;

    this.EnsureInitialized();

    this.Queue.push({
      Level,
      Message,
      Context,
      Timestamp: new Date().toISOString()
    });

    if (this.Queue.length >= this.MaxBatchSize) {
      this.Flush();
    }
  }

  private async Flush() {
    if (!this.Queue.length || !this.IsEnabled) return;

    const Batch = this.Queue.splice(0, this.MaxBatchSize);

    try {
      await fetch(LogEndpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(Batch),
        credentials: "include"
      });
    } catch (ErrorValue) {
      OriginalConsole.error("Failed to send logs to backend:", ErrorValue);
    }
  }

  private BindGlobalErrorHandlers() {
    this.HandleWindowError = (EventValue: ErrorEvent) => {
      this.error("Unhandled error", {
        Message: EventValue.message,
        Filename: EventValue.filename,
        Line: EventValue.lineno,
        Column: EventValue.colno,
        Error: NormalizeContextValue(EventValue.error)
      });
    };

    this.HandleUnhandledRejection = (EventValue: PromiseRejectionEvent) => {
      this.error("Unhandled promise rejection", {
        Reason: NormalizeContextValue(EventValue.reason)
      });
    };

    window.addEventListener("error", this.HandleWindowError);
    window.addEventListener("unhandledrejection", this.HandleUnhandledRejection);
  }

  debug(Message: string, Context?: Record<string, any>) {
    OriginalConsole.debug(Message, Context);
    this.Enqueue("debug", Message, Context);
  }

  info(Message: string, Context?: Record<string, any>) {
    OriginalConsole.info(Message, Context);
    this.Enqueue("info", Message, Context);
  }

  warn(Message: string, Context?: Record<string, any>) {
    OriginalConsole.warn(Message, Context);
    this.Enqueue("warn", Message, Context);
  }

  error(Message: string, Context?: Record<string, any>) {
    OriginalConsole.error(Message, Context);
    this.Enqueue("error", Message, Context);
  }

  destroy() {
    if (this.Timer) {
      clearInterval(this.Timer);
      this.Timer = null;
    }

    if (typeof window !== "undefined") {
      if (this.HandleWindowError) {
        window.removeEventListener("error", this.HandleWindowError);
        this.HandleWindowError = null;
      }
      if (this.HandleUnhandledRejection) {
        window.removeEventListener("unhandledrejection", this.HandleUnhandledRejection);
        this.HandleUnhandledRejection = null;
      }
    }

    this.Flush();
  }
}

export const AppLogger = new Logger();

export const InitializeFrontendLogging = () => {
  AppLogger.Initialize();
};
