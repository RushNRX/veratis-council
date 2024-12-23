import tkinter as tk
from tkinter import filedialog, scrolledtext
import fitz  # PyMuPDF
import json
import os

def pdf_to_text(pdf_path):
    try:
        # Open the PDF file
        doc = fitz.open(pdf_path)
        
        full_text = ""
        for page in doc:
            # Extract text from each page
            text = page.get_text()
            full_text += text + "\n\n"
        
        return full_text.strip()
    except Exception as e:
        return f"Error processing PDF: {str(e)}"

class PDFOCRViewer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PDF OCR Viewer")
        self.root.geometry("800x600")

        # Create and pack the Browse button
        browse_button = tk.Button(self.root, text="Browse PDF", command=self.browse_pdf)
        browse_button.pack(pady=10)

        # Create and pack the scrolled text widget
        self.text_box = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, width=80, height=30)
        self.text_box.pack(padx=10, pady=10, expand=True, fill=tk.BOTH)

    def browse_pdf(self):
        file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if file_path:
            text_content = pdf_to_text(file_path)
            self.text_box.delete(1.0, tk.END)
            self.text_box.insert(tk.END, text_content)

    def run(self):
        self.root.mainloop()

def main():
    viewer = PDFOCRViewer()
    viewer.run()

if __name__ == "__main__":
    main()