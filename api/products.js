const https = require("https");

const GITHUB_TOKEN = process.env.GITHUB_TOKEN || "";
const REPO = "joseangulovalle-cmd/discount-finder";
const FILE_PATH = "products.json";

function githubRequest(method, body = null) {
  return new Promise((resolve, reject) => {
    const data = body ? JSON.stringify(body) : null;
    const options = {
      hostname: "api.github.com",
      path: `/repos/${REPO}/contents/${FILE_PATH}`,
      method,
      headers: {
        Authorization: `token ${GITHUB_TOKEN}`,
        Accept: "application/vnd.github.v3+json",
        "Content-Type": "application/json",
        "User-Agent": "discount-finder-bot",
        ...(data ? { "Content-Length": Buffer.byteLength(data) } : {}),
      },
    };
    const req = https.request(options, (res) => {
      let raw = "";
      res.on("data", (chunk) => (raw += chunk));
      res.on("end", () => {
        try { resolve(JSON.parse(raw)); }
        catch (e) { reject(e); }
      });
    });
    req.on("error", reject);
    if (data) req.write(data);
    req.end();
  });
}

function cors(res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");
}

module.exports = async (req, res) => {
  cors(res);

  if (req.method === "OPTIONS") return res.status(200).end();

  try {
    // GET current products
    const file = await githubRequest("GET");
    const content = Buffer.from(file.content, "base64").toString();
    const data = JSON.parse(content);
    const sha = file.sha;

    if (req.method === "GET") {
      return res.status(200).json({ products: data.products });
    }

    if (req.method === "POST") {
      const { action, product } = req.body;
      const kw = (product || "").trim().toLowerCase();

      if (!kw) return res.status(400).json({ error: "product is required" });

      let products = [...data.products];

      if (action === "add") {
        if (products.length >= 6)
          return res.status(400).json({ error: "limit of 6 products reached" });
        if (!products.includes(kw)) products.push(kw);
      } else if (action === "remove") {
        products = products.filter((p) => p !== kw);
      } else {
        return res.status(400).json({ error: "action must be add or remove" });
      }

      const newContent = Buffer.from(
        JSON.stringify({ products }, null, 2)
      ).toString("base64");

      await githubRequest("PUT", {
        message: `chore: update products list`,
        content: newContent,
        sha,
      });

      return res.status(200).json({ products });
    }

    res.status(405).json({ error: "method not allowed" });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
};
