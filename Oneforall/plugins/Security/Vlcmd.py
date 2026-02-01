print("vl loaded")# -*- coding: utf-8 -*-
import os
from pyrogram import Client, filters
from pyrogram.types import Message

from Oneforall.utils.formatter import format_scan_report
from Oneforall.utils.pdf_report import generate_pdf_report
from Oneforall.utils.scanner_core import scan_website


@Client.on_message(filters.command("vlscan"))
async def vlscan_handler(client: Client, message: Message):
    """
    Command: /vlscan <website>
    Passive vulnerability scan with PDF + text report
    """

    if len(message.command) < 2:
        return await message.reply_text(
            "Usage:\n/vlscan <website>\nExample: /vlscan example.com"
        )

    target = message.command[1]
    status_msg = await message.reply_text(
        f"🔍 Starting passive vulnerability scan for {target}..."
    )

    # --- Scan ---
    result = scan_website(target)

    # --- Generate text report ---
    text_report = format_scan_report(
        domain=result["domain"],
        risk_level=result["risk"],
        score=result["score"],
        threats=result["threats"],
        recommendations=result["recommendations"],
    )

    # --- Generate PDF report ---
    pdf_path = f"/tmp/vlscan_{result['domain'].replace('.', '_')}.pdf"
    generate_pdf_report(
        file_path=pdf_path,
        domain=result["domain"],
        risk_level=result["risk"],
        score=result["score"],
        threats=result["threats"],
        recommendations=result["recommendations"],
    )

    # --- Send reports ---
    await status_msg.edit(f"✅ Scan complete! Sending reports for {target}...")

    await message.reply_text(
        f"```\n{text_report}\n```",
        disable_web_page_preview=True,
    )

    await message.reply_document(
        pdf_path,
        caption="📄 Vulnerability Scan Report (PDF)",
    )

    # Clean up temp file
    if os.path.exists(pdf_path):
        os.remove(pdf_path)

    await status_msg.delete()
