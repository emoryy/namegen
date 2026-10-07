// Reads one JSON request on stdin, prints a JSON array of raw candidates on stdout.
//   {"engine": "markov", "words": [...], "n": 300, "seed": 1, "order": 3, "prior": 0.01, "backoff": true, "minLength": 4, "maxLength": 9, "startsWith": "tre"}
//   {"engine": "lexifer", "def": "<.def file text>", "n": 300, "seed": 1}
import { createRequire } from "node:module";
import { NameGenerator } from "@ksilvennoinen/markov-namegen";

const require = createRequire(import.meta.url);

function mulberry32(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function markov(req, random) {
  const gen = new NameGenerator(req.words, req.order ?? 3, req.prior ?? 0.01, req.backoff ?? true, random);
  return gen.generateNames(req.n, {
    minLength: req.minLength ?? 4,
    maxLength: req.maxLength ?? 10,
    startsWith: req.startsWith ?? "",
    maxTimePerName: 50,
  });
}

function lexifer(req, random) {
  // Lexifer has no seed parameter and draws from Math.random directly.
  Math.random = random;
  const run = require("lexifer");
  const errors = [];
  const out = run(req.def, req.n, false, true, true, (e) => errors.push(String(e)));
  if (errors.length) process.stderr.write(errors.join("\n") + "\n");
  return out.split("\n").map((w) => w.trim()).filter(Boolean);
}

let input = "";
for await (const chunk of process.stdin) input += chunk;
const req = JSON.parse(input);
const random = mulberry32(req.seed ?? Date.now());
const engines = { markov, lexifer };
if (!engines[req.engine]) {
  process.stderr.write(`unknown engine: ${req.engine}\n`);
  process.exit(2);
}
process.stdout.write(JSON.stringify(engines[req.engine](req, random)));
