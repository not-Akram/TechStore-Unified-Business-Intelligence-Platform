# Tesseract OCR Engine Installation Guide

This guide explains how to install and configure the **Tesseract OCR engine**, which is required for the OCR (Legacy Invoices) part of the Business Intelligence project.

---

## Step 1: Download Tesseract OCR

Download the Windows installer from the official repository:

👉 https://github.com/UB-Mannheim/tesseract/wiki

Choose the **latest 64-bit installer** (recommended).

---

## Step 2: Install and Select Languages

During the installation wizard:

1. Proceed with the default installation settings.
2. When prompted to select languages, make sure to include:
   - **English (eng)**
   - **French (fra)** (required for invoice recognition)
3. Continue until the installation is completed.

---

## Step 3: Add Tesseract to Environment Variables

After installation, you must add the Tesseract installation folder to the system PATH.

1. Open **System Properties** → **Environment Variables**
2. Under **System variables**, select `Path` and click **Edit**
3. Add the following directory:




4. Click **OK** and restart your terminal or IDE.

---

> **Verification**  
> Open Command Prompt and run:
>
> ```
> tesseract --version
> ```
>
> If version information is displayed, the installation was successful.

---

Once completed, Tesseract will be ready to use with `pytesseract` in Python for OCR tasks.
