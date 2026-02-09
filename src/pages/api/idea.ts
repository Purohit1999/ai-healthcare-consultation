import type { NextApiRequest, NextApiResponse } from "next";
import OpenAI from "openai";

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  try {
    const apiKey = process.env.OPENAI_API_KEY;
    if (!apiKey) {
      res.status(500).send("ERROR: OPENAI_API_KEY is missing in environment variables.");
      return;
    }

    const client = new OpenAI({ apiKey });

    const prompt = `
Generate ONE SaaS-ready business idea for an AI Agent.

Return the response in Markdown using this exact structure:
# Title
**Problem:**
**Solution:**
**Target Customers:**
**Why it Works:**

Constraints:
- Practical and realistic
- No buzzwords
- Under 120 words
`;

    const response = await client.chat.completions.create({
      model: "gpt-5-nano",
      messages: [{ role: "user", content: prompt }],
    });

    res.setHeader("Content-Type", "text/plain; charset=utf-8");
    res.status(200).send(response.choices[0].message.content ?? "");
  } catch (e: any) {
    res.status(500).send(`ERROR: ${e?.message ?? "Unknown error"}`);
  }
}
