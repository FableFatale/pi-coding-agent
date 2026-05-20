/**
 * Pi Test Runner - 自动测试生成和运行
 */

import { spawn } from "child_process";
import { join } from "path";
import { readFile, writeFile, mkdir } from "fs/promises";
import { existsSync } from "fs";

export interface TestFramework {
  name: string;
  extension: string;
  testPattern: RegExp;
  command: string[];
  generateTemplate: (sourceFile: string) => string;
}

const FRAMEWORKS: Record<string, TestFramework> = {
  jest: {
    name: "Jest",
    extension: ".test.ts",
    testPattern: /\.test\.(ts|js)$/,
    command: ["npx", "jest"],
    generateTemplate: (source) => `import { describe, it, expect } from 'jest';

describe('${source}', () => {
  it('should work', () => {
    expect(true).toBe(true);
  });
});
`
  },
  vitest: {
    name: "Vitest",
    extension: ".test.ts",
    testPattern: /\.test\.(ts|js)$/,
    command: ["npx", "vitest"],
    generateTemplate: (source) => `import { describe, it, expect } from 'vitest';

describe('${source}', () => {
  it('should work', () => {
    expect(true).toBe(true);
  });
});
`
  },
  pytest: {
    name: "Pytest",
    extension: "_test.py",
    testPattern: /_test\.py$/,
    command: ["pytest"],
    generateTemplate: (source) => `import pytest

def test_${source.replace(/\.py$/, '')}():
    assert True
`
  },
  gotest: {
    name: "Go Test",
    extension: "_test.go",
    testPattern: /_test\.go$/,
    command: ["go", "test", "./..."],
    generateTemplate: (source) => `package main

import "testing"

func Test${source.replace(/\.go$/, '').replace(/^./, (c) => c.toUpperCase())}(t *testing.T) {
    t.Log("Test placeholder")
}
`
  }
};

export async function detectFramework(projectPath: string): Promise<TestFramework | null> {
  const pkgPath = join(projectPath, "package.json");
  
  if (existsSync(pkgPath)) {
    const pkg = JSON.parse(await readFile(pkgPath, "utf-8"));
    const deps = { ...pkg.dependencies, ...pkg.devDependencies };
    
    if (deps.vitest) return FRAMEWORKS.vitest;
    if (deps.jest) return FRAMEWORKS.jest;
  }
  
  const goMod = join(projectPath, "go.mod");
  if (existsSync(goMod)) return FRAMEWORKS.gotest;
  
  const pytestIni = join(projectPath, "pytest.ini");
  const setupPy = join(projectPath, "setup.py");
  if (existsSync(pytestIni) || existsSync(setupPy)) return FRAMEWORKS.pytest;
  
  return FRAMEWORKS.jest; // default
}

export async function generateTest(
  sourceFile: string,
  framework: TestFramework
): Promise<string> {
  const baseName = sourceFile.replace(/\.[^.]+$/, "");
  const testFile = baseName + framework.extension;
  
  if (!existsSync(testFile)) {
    const testDir = join(testFile, "..");
    await mkdir(testDir, { recursive: true });
    await writeFile(testFile, framework.generateTemplate(baseName), "utf-8");
  }
  
  return testFile;
}

export async function runTests(
  projectPath: string,
  framework: TestFramework,
  options: { coverage?: boolean; watch?: boolean } = {}
): Promise<{ stdout: string; stderr: string; exitCode: number }> {
  const args = [...framework.command];
  
  if (options.coverage) {
    if (framework.name === "Jest") args.push("--coverage");
    if (framework.name === "Vitest") args.push("--coverage");
    if (framework.name === "Pytest") args.push("--cov");
  }
  
  if (options.watch) {
    if (framework.name === "Jest") args.push("--watch");
    if (framework.name === "Vitest") args.push("--watch");
    if (framework.name === "Pytest") args.push("-k", "not slow", "--rerun");
  }
  
  return new Promise((resolve, reject) => {
    const proc = spawn(args[0], args.slice(1), {
      cwd: projectPath,
      shell: true
    });
    
    let stdout = "";
    let stderr = "";
    
    proc.stdout?.on("data", (d) => { stdout += d.toString(); });
    proc.stderr?.on("data", (d) => { stderr += d.toString(); });
    
    proc.on("close", (code) => {
      resolve({ stdout, stderr, exitCode: code || 0 });
    });
    
    proc.on("error", reject);
  });
}
