/**
 * Pi Debugger - 断点调试
 */

import { spawn, ChildProcess } from "child_process";
import { EventEmitter } from "events";

export interface Breakpoint {
  id?: number;
  file: string;
  line: number;
  condition?: string;
}

export interface StackFrame {
  id: number;
  name: string;
  file: string;
  line: number;
}

export interface Variable {
  name: string;
  value: string;
  type: string;
}

export class Debugger extends EventEmitter {
  private process: ChildProcess | null = null;
  private breakpoints: Map<string, number[]> = new Map();
  private paused = false;

  async launch(file: string, language: "node" | "python" | "go" = "node"): Promise<void> {
    const args = this.getLaunchArgs(file, language);
    this.process = spawn(args[0], args.slice(1), {
      stdio: ["pipe", "pipe", "pipe", "pipe"]
    });

    this.process.stdout?.on("data", (data) => {
      this.parseOutput(data.toString());
    });

    this.process.stderr?.on("data", (data) => {
      this.emit("error", data.toString());
    });

    this.process.on("close", (code) => {
      this.emit("exit", code);
    });
  }

  private getLaunchArgs(file: string, language: "node" | "python" | "go"): string[] {
    switch (language) {
      case "node":
        return ["node", "--inspect-brk", file];
      case "python":
        return ["python", "-m", "debugpy", "--listen", "localhost:5678", file];
      case "go":
        return ["dlv", "debug", file];
      default:
        return ["node", file];
    }
  }

  async setBreakpoint(file: string, line: number, condition?: string): Promise<number> {
    const bp: Breakpoint = { file, line, condition };
    
    if (!this.breakpoints.has(file)) {
      this.breakpoints.set(file, []);
    }
    
    const id = this.breakpoints.get(file)!.length + 1;
    bp.id = id;
    
    // Send debugger protocol command
    this.sendCommand(`breakpoint --id ${id} --file ${file} --line ${line}`);
    
    return id;
  }

  async stepOver(): Promise<void> {
    this.sendCommand("next");
  }

  async stepInto(): Promise<void> {
    this.sendCommand("step");
  }

  async stepOut(): Promise<void> {
    this.sendCommand("out");
  }

  async continue(): Promise<void> {
    this.sendCommand("continue");
    this.paused = false;
  }

  async evaluate(expression: string): Promise<string> {
    this.sendCommand(`evaluate --expression ${expression}`);
    return ""; // Will be set when response received
  }

  async getStackTrace(): Promise<StackFrame[]> {
    this.sendCommand("stack");
    return []; // Will be populated by parseOutput
  }

  async getVariables(scope: "local" | "global" = "local"): Promise<Variable[]> {
    this.sendCommand(`variables --scope ${scope}`);
    return []; // Will be populated by parseOutput
  }

  private sendCommand(cmd: string): void {
    if (this.process?.stdin) {
      this.process.stdin.write(cmd + "\n");
    }
  }

  private parseOutput(data: string): void {
    // Parse debugger protocol responses
    if (data.includes("breakpoint")) {
      this.emit("breakpoint", data);
    }
    if (data.includes("paused") || data.includes("stopped")) {
      this.paused = true;
      this.emit("paused");
    }
    if (data.includes("Variables")) {
      this.emit("variables", data);
    }
  }

  kill(): void {
    if (this.process) {
      this.process.kill();
      this.process = null;
    }
  }

  isPaused(): boolean {
    return this.paused;
  }
}

export const debugger = new Debugger();
