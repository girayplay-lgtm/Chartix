const express = require("express");
const path = require("path");
const { spawn } = require("child_process");

const app = express();
const PORT = process.env.PORT || 3000;

const CACHE_MS = 15000;
const MEMORY = new Map();

app.use(express.static(path.join(__dirname, "public")));

function normalize(symbol) {
  return String(symbol || "AAPL").trim().toUpperCase();
}

function normalizeRange(range) {
  const r = String(range || "1D").trim().toUpperCase();
  return ["1D", "5D", "1W", "1M"].includes(r) ? r : "1D";
}

function runPythonWith(command, symbol, range) {
  return new Promise((resolve, reject) => {
    console.log("Trying:", command, "data_service.py", symbol, range);

    const child = spawn(command, ["data_service.py", symbol, range], {
      cwd: __dirname,
      windowsHide: true
    });

    let stdout = "";
    let stderr = "";

    const timer = setTimeout(() => {
      child.kill();
      reject(new Error("Data request timed out."));
    }, 45000);

    child.stdout.on("data", data => {
      stdout += data.toString();
    });

    child.stderr.on("data", data => {
      stderr += data.toString();
    });

    child.on("error", err => {
      clearTimeout(timer);
      reject(err);
    });

    child.on("close", code => {
      clearTimeout(timer);

      console.log("Python exit code:", code);
      if (stderr) console.log("Python stderr:", stderr);
      if (stdout) console.log("Python stdout:", stdout.slice(0, 500));

      if (code !== 0) {
        try {
          const json = JSON.parse(stdout);
          reject(new Error(json.error || json.trace || "Python failed."));
        } catch {
          reject(new Error(stderr || stdout || "Python failed."));
        }
        return;
      }

      try {
        const json = JSON.parse(stdout);

        if (json.error) {
          reject(new Error(json.error));
          return;
        }

        resolve(json);
      } catch {
        reject(new Error("Python output is not valid JSON."));
      }
    });
  });
}

async function runPython(symbol, range) {
  const commands = process.platform === "win32"
    ? ["py", "python"]
    : ["python3", "python"];

  let lastError = null;

  for (const command of commands) {
    try {
      return await runPythonWith(command, symbol, range);
    } catch (err) {
      lastError = err;
      console.log("Command failed:", command, err.message);
    }
  }

  throw new Error(lastError ? lastError.message : "Python data service failed.");
}

app.get("/api/details", async (req, res) => {
  try {
    const symbol = normalize(req.query.symbol);
    const range = normalizeRange(req.query.range);
    const cacheKey = `${symbol}:${range}`;

    const cached = MEMORY.get(cacheKey);

    if (cached && Date.now() - cached.savedAt < CACHE_MS) {
      return res.json({
        ok: true,
        source: "memory",
        data: cached.data
      });
    }

    const data = await runPython(symbol, range);

    MEMORY.set(cacheKey, {
      data,
      savedAt: Date.now()
    });

    res.json({
      ok: true,
      source: "fresh",
      data
    });
  } catch (err) {
    console.error("API error:", err.message);

    res.status(500).json({
      ok: false,
      error: err.message
    });
  }
});

app.get("/api/clear-cache", (req, res) => {
  MEMORY.clear();
  res.json({ ok: true, message: "Cache cleared." });
});

app.get("/api/memory", (req, res) => {
  res.json({
    ok: true,
    keys: Array.from(MEMORY.keys())
  });
});

app.get("/health", (req, res) => {
  res.json({
    ok: true,
    message: "CHARTIX server running.",
    port: PORT,
    ranges: ["1D", "5D", "1W", "1M"]
  });
});

app.listen(PORT, () => {
  console.log("CHARTIX running on port " + PORT);
  console.log("Chart ranges enabled: 1D, 5D, 1W, 1M");
});