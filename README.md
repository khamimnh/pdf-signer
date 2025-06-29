# PDF Digital Signature

A professional desktop application for adding digital signatures and text to PDF documents with an intuitive graphical interface.

![PDF Digital Signature](https://img.shields.io/badge/Python-3.11+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)

## 🌟 Features

### 📄 PDF Management
- **Multi-page PDF support** - Navigate through multiple pages
- **Auto-save with naming convention** - Files saved as `[original]_signed_by_[username].pdf`
- **Optimized file size** - Compressed output to minimize file bloat
- **Real-time preview** - See changes instantly

### ✍️ Signature & Text Tools
- **Image Signatures** - Upload and use PNG, JPG, JPEG, GIF, BMP files
- **Text Elements** - Add custom text with full color customization
- **Signature Library** - Save and reuse frequently used signatures
- **Color Picker** - Full color palette for text customization
- **Auto timestamp** - Automatic "Signed by [Name] at [Date/Time]" on image signatures

### 🎛️ User Interface
- **Resizable sidebar** - Drag to adjust panel sizes
- **Scrollable controls** - Handle long content lists
- **Status notifications** - Color-coded status bar with auto-hide
- **Keyboard shortcuts** - Ctrl+O (Open), Ctrl+S (Save)
- **Clean, professional design** - No visual clutter

### 🖱️ Interactive Controls
- **Drag & Drop** - Move signatures and text around the document
- **Ctrl+Scroll Resize** - Easy resizing with mouse wheel
- **Double-click Edit** - Quick text editing
- **Visual Selection** - Clear selection borders and handles
- **Element Management** - List and manage all added elements

## 🚀 Installation

### Prerequisites
- Python 3.11 or higher
- Required packages (see requirements.txt)

### Setup
1. **Clone or download** the application files
```bash
git clone [repository-url]
cd pdf-digital-signature
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Run the application**
```bash
python app.py
```

## 📋 Requirements

```txt
PyMuPDF>=1.23.0
Pillow>=10.0.0
reportlab>=4.0.0
```

## 🎮 Usage Guide

### Getting Started
1. **Launch** the application - it will open maximized
2. **Open a PDF** using "Open PDF" button or `Ctrl+O`
3. **Navigate** between pages using Previous/Next buttons

### Adding Text
1. **Choose text color** using the color picker in "Add Text" section
2. **Click "Add Text"** - a text element appears on the page
3. **Edit immediately** - the text becomes editable automatically
4. **Move and resize** - drag to move, Ctrl+scroll to resize

### Adding Signatures
1. **Click "Add Image Signature"**
2. **Select image file** from your computer
3. **Choose to save** - optionally save to signature library for reuse
4. **Position and resize** - drag and Ctrl+scroll to adjust

### Using Saved Signatures
1. **Select signature** from dropdown in "Saved Signatures" section
2. **Click "Use"** to add to current page
3. **Preview** to see signature before using
4. **Delete** to remove from library

### Customizing Elements
1. **Select element** by clicking on it
2. **Change text color** in "Selected Element Properties"
3. **Resize** with Ctrl+scroll wheel
4. **Move** by dragging

### Saving Your Work
1. **Press Ctrl+S** or click "Save Signed PDF"
2. **File automatically saved** in same folder with `_signed_by_[username]` suffix
3. **Success notification** appears in status bar

## ⚙️ Configuration

### Signature Name
- **Default**: Uses your system username
- **Customizable**: Change in "Signature Settings" section
- **Persistent**: Saved between sessions

### File Storage
- **Signatures saved** in `saved_signatures/` folder
- **Settings stored** in `signatures.json`
- **Auto-created** on first run

## 🎯 Tips & Shortcuts

### Keyboard Shortcuts
- `Ctrl+O` - Open PDF
- `Ctrl+S` - Save signed PDF
- `Escape` - Cancel text editing
- `Enter` - Finish text editing

### Mouse Controls
- **Single click** - Select element
- **Double-click** - Edit text
- **Drag** - Move element
- **Ctrl+Scroll** - Resize element
- **Mouse wheel** - Scroll sidebar

### Best Practices
- **Use high-quality images** for signatures (PNG recommended)
- **Keep signature library organized** - use descriptive names
- **Test positioning** before final save
- **Use consistent colors** for professional appearance

## 🔧 Troubleshooting

### Common Issues

**PDF won't open**
- Ensure PDF is not password-protected
- Check file is not corrupted
- Verify file permissions

**Signature appears blurry**
- Use higher resolution images
- Avoid over-resizing signatures
- Use PNG format for best quality

**Application won't start**
- Check Python version (3.11+ required)
- Verify all dependencies installed
- Run `pip install -r requirements.txt`

**Text color not changing**
- Ensure text element is selected
- Try selecting different text element
- Check color picker is working

### Debug Mode
- Console output shows debug information
- Check terminal for error messages
- Report issues with console output

## 📁 File Structure

```
pdf-digital-signature/
├── app.py                 # Main application
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── icon.png              # Application icon (optional)
└── saved_signatures/     # Auto-created folder
    ├── signatures.json   # Signature library
    └── *.png            # Saved signature images
```

## 🔄 Version History

### Latest Version
- ✅ Resizable and scrollable sidebar
- ✅ Full color picker for text
- ✅ Clean interface without icons
- ✅ Auto username detection
- ✅ Enhanced keyboard shortcuts
- ✅ Color-coded status notifications

### Key Features Added
- Professional color picker interface
- Optimized PDF file size handling
- Enhanced element management
- Improved user experience

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📞 Support

For support, please:
1. Check this README for solutions
2. Review console output for errors
3. Report issues with detailed information

## 🙏 Acknowledgments

- **PyMuPDF** - PDF processing
- **Pillow** - Image handling
- **Tkinter** - GUI framework
- **ReportLab** - PDF optimization

---

**Made with ❤️ for professional PDF signing needs**
