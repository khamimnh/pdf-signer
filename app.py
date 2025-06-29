import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog
import fitz  # PyMuPDF
from PIL import Image, ImageTk, ImageDraw, ImageFont
import io
import json
import os
import getpass
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class SignatureElement:
    element_type: str  # 'image' atau 'text'
    content: any  # Image object atau string
    x: float
    y: float
    width: float
    height: float
    page_num: int
    canvas_id: int = None  # ID untuk tracking di canvas
    text_color: str = 'black'  # Default text color

class PDFSignatureApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Digital Signature")
        
        # Set window icon
        try:
            if os.path.exists("icon.png"):
                icon_image = tk.PhotoImage(file="icon.png")
                self.root.iconphoto(True, icon_image)
        except Exception as e:
            print(f"Could not load icon: {e}")
        
        self.root.state('zoomed')  # Maximize window on Windows
        # For cross-platform compatibility
        try:
            self.root.wm_state('zoomed')  # Windows
        except:
            self.root.attributes('-zoomed', True)  # Linux
        
        # Variables
        self.pdf_doc = None
        self.pdf_file_path = None
        self.signature_elements = []
        self.current_page = 0
        self.selected_element = None
        self.drag_data = {"x": 0, "y": 0}
        self.is_editing_text = False
        self.text_entry = None
        
        # Canvas settings
        self.canvas_width = 700
        self.page_scale_factor = 1.0
        self.zoom_level = 1.0  # Add zoom level tracking
        
        # Signature storage
        self.signatures_dir = "saved_signatures"
        self.saved_signatures = {}
        self.signature_name = getpass.getuser().upper()  # Get current username
        
        # Initialize
        self.ensure_directories()
        self.load_saved_signatures()
        self.create_ui()
        self.setup_keyboard_shortcuts()
        
    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts"""
        # Ctrl+O for Open PDF
        self.root.bind('<Control-o>', lambda e: self.open_pdf())
        self.root.bind('<Control-O>', lambda e: self.open_pdf())
        
        # Ctrl+S for Save PDF
        self.root.bind('<Control-s>', lambda e: self.save_pdf())
        self.root.bind('<Control-S>', lambda e: self.save_pdf())
    
    def ensure_directories(self):
        """Create necessary directories"""
        if not os.path.exists(self.signatures_dir):
            os.makedirs(self.signatures_dir)
    
    def load_saved_signatures(self):
        """Load saved signatures and settings"""
        try:
            signatures_file = os.path.join(self.signatures_dir, "signatures.json")
            if os.path.exists(signatures_file):
                with open(signatures_file, 'r') as f:
                    data = json.load(f)
                
                # Load signature name if exists
                if isinstance(data, dict) and 'signature_name' in data:
                    self.signature_name = data.get('signature_name', getpass.getuser().upper())
                    signature_list = data.get('signatures', [])
                else:
                    # Old format compatibility
                    signature_list = data if isinstance(data, list) else []
                
                # Load signature images
                for sig_info in signature_list:
                    try:
                        img_path = os.path.join(self.signatures_dir, sig_info['filename'])
                        if os.path.exists(img_path):
                            img = Image.open(img_path)
                            if img.mode != 'RGBA':
                                img = img.convert('RGBA')
                            self.saved_signatures[sig_info['name']] = img
                    except Exception as e:
                        print(f"Error loading signature {sig_info['name']}: {e}")
        except Exception as e:
            print(f"Error loading saved signatures: {e}")
    
    def save_settings(self):
        """Save settings and signature list"""
        try:
            signatures_file = os.path.join(self.signatures_dir, "signatures.json")
            
            # Create signature list
            signature_list = []
            for name in self.saved_signatures.keys():
                signature_list.append({
                    'name': name,
                    'filename': f"{name}.png"
                })
            
            # Save data with signature name
            data = {
                'signature_name': self.signature_name,
                'signatures': signature_list
            }
            
            with open(signatures_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def save_signature_to_library(self, image, name):
        """Save signature to library"""
        try:
            filename = f"{name}.png"
            img_path = os.path.join(self.signatures_dir, filename)
            image.save(img_path, format='PNG')
            
            self.saved_signatures[name] = image
            self.save_settings()
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save signature: {e}")
    
    def create_ui(self):
        """Create the user interface"""
        # Main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Left panel for controls
        left_frame = ttk.Frame(main_container, width=350)
        left_frame.pack(side='left', fill='y', padx=(0, 10))
        left_frame.pack_propagate(False)
        
        # Right panel for PDF viewer
        right_frame = ttk.Frame(main_container)
        right_frame.pack(side='right', fill='both', expand=True)
        
        self.create_control_panel(left_frame)
        self.create_pdf_viewer(right_frame)
        self.create_status_bar()
    
    def create_status_bar(self):
        """Create status bar for notifications"""
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.pack(side='bottom', fill='x', padx=10, pady=(0, 10))
        
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(self.status_frame, textvariable=self.status_var, 
                                     relief='sunken', anchor='w', 
                                     background='lightgray', foreground='black')
        self.status_label.pack(fill='x', ipady=5)
    
    def show_status(self, message, duration=3000):
        """Show status message in status bar with color change"""
        self.status_var.set(message)
        
        # Change to green for new notifications
        self.status_label.configure(background='lightgreen')
        
        # After 2 seconds, change back to gray
        self.root.after(2000, lambda: self.status_label.configure(background='lightgray'))
        
        # Reset to "Ready" after duration
        self.root.after(duration, lambda: self.status_var.set("Ready"))
    
    def create_control_panel(self, parent):
        """Create control panel"""
        # File operations
        file_frame = ttk.LabelFrame(parent, text="File Operations", padding=10)
        file_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Button(file_frame, text="Open (Ctrl+O)", 
                  command=self.open_pdf, width=25).pack(pady=2)
        ttk.Button(file_frame, text="Save (Ctrl+S)", 
                  command=self.save_pdf, width=25).pack(pady=2)
        
        # Page navigation
        nav_frame = ttk.LabelFrame(parent, text="Page Navigation", padding=10)
        nav_frame.pack(fill='x', pady=(0, 10))
        
        self.page_var = tk.StringVar(value="No PDF loaded")
        ttk.Label(nav_frame, textvariable=self.page_var, 
                 font=('Arial', 10, 'bold')).pack(pady=5)
        
        nav_buttons = ttk.Frame(nav_frame)
        nav_buttons.pack(fill='x', pady=5)
        ttk.Button(nav_buttons, text="◀ Previous", 
                  command=self.prev_page).pack(side='left', padx=(0, 5))
        ttk.Button(nav_buttons, text="Next ▶", 
                  command=self.next_page).pack(side='right', padx=(5, 0))
        
        # Zoom controls
        zoom_frame = ttk.LabelFrame(parent, text="Zoom", padding=10)
        zoom_frame.pack(fill='x', pady=(0, 10))
        
        self.zoom_var = tk.StringVar(value="100%")
        ttk.Label(zoom_frame, textvariable=self.zoom_var, 
                 font=('Arial', 10, 'bold')).pack(pady=5)
        
        zoom_buttons = ttk.Frame(zoom_frame)
        zoom_buttons.pack(fill='x')
        ttk.Button(zoom_buttons, text="Zoom In (+)", 
                  command=self.zoom_in).pack(side='left', padx=(0, 5))
        ttk.Button(zoom_buttons, text="Zoom Out (-)", 
                  command=self.zoom_out).pack(side='left', padx=(0, 5))
        ttk.Button(zoom_buttons, text="Reset", 
                  command=self.zoom_reset).pack(side='left')
                
        # Text 
        text_frame = ttk.LabelFrame(parent, text="Add Text", padding=10)
        text_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Button(text_frame, text="Add Text", 
                  command=self.add_text_signature, width=25).pack()
        
        # Signature operations - Combined frame
        sig_frame = ttk.LabelFrame(parent, text="Signatures", padding=10)
        sig_frame.pack(fill='x', pady=(0, 10))
        
        # Top section: Add signature button and combobox side by side
        top_sig_frame = ttk.Frame(sig_frame)
        top_sig_frame.pack(fill='x', pady=(0, 10))
        
        # Add Image Signature button on the left
        ttk.Button(top_sig_frame, text="Add Image", 
                  command=self.add_image_signature).pack(side='left', padx=(0, 5))
        
        # Saved signatures combobox on the right
        self.signature_var = tk.StringVar()
        self.signature_combo = ttk.Combobox(top_sig_frame, textvariable=self.signature_var, 
                                          state="readonly", width=15)
        self.signature_combo.pack(side='left', fill='x', expand=True)
        
        # Bottom section: Saved signature buttons
        saved_buttons = ttk.Frame(sig_frame)
        saved_buttons.pack(fill='x')
        ttk.Button(saved_buttons, text="Use", 
                  command=self.use_saved_signature).pack(side='left', padx=(0, 2))
        ttk.Button(saved_buttons, text="Delete", 
                  command=self.delete_signature).pack(side='left', padx=2)
        ttk.Button(saved_buttons, text="Preview", 
                  command=self.preview_signature).pack(side='right')
        
        self.update_signature_combo()
        
        # Signature name setting
        name_frame = ttk.LabelFrame(parent, text="Signature Settings", padding=10)
        name_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(name_frame, text="Signature Name:").pack(anchor='w')
        
        # Name input frame (entry + button side by side)
        name_input_frame = ttk.Frame(name_frame)
        name_input_frame.pack(fill='x')
        
        self.name_var = tk.StringVar(value=self.signature_name)
        name_entry = ttk.Entry(name_input_frame, textvariable=self.name_var)
        name_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))
        
        ttk.Button(name_input_frame, text="Save Name", 
                  command=self.save_signature_name).pack(side='left')
        
        # Element properties (for selected element)
        props_frame = ttk.LabelFrame(parent, text="Selected Element Properties", padding=10)
        props_frame.pack(fill='x', pady=(0, 10))
        
        # Text color change for selected text element
        color_change_frame = ttk.Frame(props_frame)
        color_change_frame.pack(fill='x', pady=(0, 5))
        ttk.Label(color_change_frame, text="Change Text Color:").pack(side='left', padx=(0, 5))
        
        # Define color options
        color_colors = ['black', 'red', 'blue', 'green', 'purple', 'orange', 'brown', 'gray']
        
        self.selected_color_var = tk.StringVar(value='black')
        self.selected_color_combo = ttk.Combobox(color_change_frame, textvariable=self.selected_color_var, 
                                                values=color_colors, state="readonly", width=10)
        self.selected_color_combo.pack(side='left', padx=(0, 5))
        
        ttk.Button(color_change_frame, text="Apply", 
                  command=self.change_selected_text_color).pack(side='left')
        
        # Element management
        mgmt_frame = ttk.LabelFrame(parent, text="Manage Elements", padding=10)
        mgmt_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Button(mgmt_frame, text="Delete Selected", 
                  command=self.delete_selected, width=25).pack(pady=2)
        ttk.Button(mgmt_frame, text="Clear All", 
                  command=self.clear_all, width=25).pack(pady=2)
        
        # Element list
        self.element_listbox = tk.Listbox(mgmt_frame, height=6)
        self.element_listbox.pack(fill='x', pady=5)
        self.element_listbox.bind('<<ListboxSelect>>', self.on_element_select)
    
    def create_pdf_viewer(self, parent):
        """Create PDF viewer"""
        # Title
        # title_frame = ttk.Frame(parent)
        # title_frame.pack(fill='x', pady=(0, 10))
        # ttk.Label(title_frame, text="PDF Viewer", 
        #          font=('Arial', 12, 'bold')).pack()
        
        # Canvas with scrollbars
        canvas_frame = ttk.Frame(parent)
        canvas_frame.pack(fill='both', expand=True)
        
        # Create canvas
        self.canvas = tk.Canvas(canvas_frame, bg='#EAEAEA', 
                               width=self.canvas_width, height=600)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient='vertical', 
                                   command=self.canvas.yview)
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient='horizontal', 
                                   command=self.canvas.xview)
        
        self.canvas.configure(yscrollcommand=v_scrollbar.set, 
                             xscrollcommand=h_scrollbar.set)
        
        # Pack widgets properly
        v_scrollbar.pack(side='right', fill='y')
        h_scrollbar.pack(side='bottom', fill='x')
        self.canvas.pack(side='left', fill='both', expand=True)
        
        # Bind events
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.canvas.bind("<Control-MouseWheel>", self.on_ctrl_scroll)
        self.canvas.bind("<MouseWheel>", self.on_scroll)
        self.canvas.bind("<Double-Button-1>", self.on_double_click)
        
        # Bind keyboard shortcuts for zoom
        self.root.bind('<Control-plus>', lambda e: self.zoom_in())
        self.root.bind('<Control-equal>', lambda e: self.zoom_in())  # For keyboards without numpad
        self.root.bind('<Control-minus>', lambda e: self.zoom_out())
        self.root.bind('<Control-0>', lambda e: self.zoom_reset())
        
        # Focus for keyboard events
        self.canvas.focus_set()
        
        # Initial message
        self.canvas.create_text(self.canvas_width//2, 300, 
                               text="Click 'Open PDF' to start\n\nTips:\n• Click signature to select\n• Double-click text to edit\n• Ctrl+Scroll to resize\n• Drag to move", 
                               font=('Arial', 12), fill='gray', justify='center')
    
    def zoom_in(self):
        """Zoom in the PDF preview"""
        if self.pdf_doc:
            self.zoom_level = min(3.0, self.zoom_level * 1.2)  # Max 300% zoom
            self.update_page_display()
            self.zoom_var.set(f"{int(self.zoom_level * 100)}%")
            self.show_status(f"Zoomed to {int(self.zoom_level * 100)}%")
    
    def zoom_out(self):
        """Zoom out the PDF preview"""
        if self.pdf_doc:
            self.zoom_level = max(0.5, self.zoom_level / 1.2)  # Min 50% zoom
            self.update_page_display()
            self.zoom_var.set(f"{int(self.zoom_level * 100)}%")
            self.show_status(f"Zoomed to {int(self.zoom_level * 100)}%")
    
    def zoom_reset(self):
        """Reset zoom to 100%"""
        if self.pdf_doc:
            self.zoom_level = 1.0
            self.update_page_display()
            self.zoom_var.set("100%")
            self.show_status("Zoom reset to 100%")
    
    def save_signature_name(self):
        """Save signature name setting"""
        new_name = self.name_var.get().strip()
        if new_name:
            self.signature_name = new_name
            self.save_settings()
            self.show_status(f"Signature name saved: {new_name}")
        else:
            self.show_status("Please enter a valid name", 2000)
    
    def open_pdf(self):
        """Open PDF file"""
        file_path = filedialog.askopenfilename(
            title="Select PDF file",
            filetypes=[("PDF files", "*.pdf")]
        )
        
        if file_path:
            try:
                print(f"DEBUG: Opening PDF: {file_path}")  # Debug info
                
                if self.pdf_doc:
                    self.pdf_doc.close()
                
                self.pdf_doc = fitz.open(file_path)
                self.pdf_file_path = file_path
                self.current_page = 0
                self.signature_elements.clear()
                self.selected_element = None
                self.zoom_level = 1.0  # Reset zoom when opening new PDF
                self.zoom_var.set("100%")
                
                print(f"DEBUG: PDF opened successfully. Pages: {len(self.pdf_doc)}")  # Debug info
                
                # Clear any existing photo references
                if hasattr(self, 'photo_refs'):
                    self.photo_refs.clear()
                
                self.update_page_display()
                self.update_element_list()
                
                self.show_status(f"PDF loaded successfully! Pages: {len(self.pdf_doc)}")
                
            except Exception as e:
                print(f"DEBUG: Error opening PDF: {e}")  # Debug info
                self.show_status(f"Failed to open PDF: {str(e)}", 5000)
    
    def update_page_display(self):
        """Update page display"""
        if not self.pdf_doc:
            return
        
        try:
            # Clear selection when changing pages
            self.selected_element = None
            self.canvas.delete("selection_border")
            
            # Update page info
            total_pages = len(self.pdf_doc)
            self.page_var.set(f"Page {self.current_page + 1} of {total_pages}")
            
            # Get page
            page = self.pdf_doc[self.current_page]
            page_rect = page.rect
            
            print(f"DEBUG: Page rect: {page_rect.width} x {page_rect.height}")  # Debug info
            
            # Calculate scale to fit canvas width (without zoom)
            base_scale = self.canvas_width / page_rect.width if page_rect.width > 0 else 1.0
            
            # Apply zoom level to get final scale
            self.page_scale_factor = base_scale * self.zoom_level
            
            # Store base scale for saving
            self.base_scale_factor = base_scale
            
            print(f"DEBUG: Scale factor: {self.page_scale_factor}")  # Debug info
            
            # Render page with proper scaling
            mat = fitz.Matrix(self.page_scale_factor, self.page_scale_factor)
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            
            # Convert to PIL Image and then to PhotoImage
            pil_image = Image.open(io.BytesIO(img_data))
            self.current_pil_image = pil_image.copy()
            
            print(f"DEBUG: Image size: {pil_image.size}")  # Debug info
            
            # Clear canvas and create new image
            self.canvas.delete("all")
            
            # Create PhotoImage
            self.photo_image = ImageTk.PhotoImage(pil_image)
            
            # Calculate center position for PDF
            canvas_center_x = self.canvas_width // 2
            image_center_x = pil_image.width // 2
            x_offset = max(0, canvas_center_x - image_center_x)
            
            # Create image centered horizontally
            self.canvas.create_image(x_offset, 0, anchor='nw', image=self.photo_image, tags="pdf_page")
            
            # Update scroll region
            canvas_height = int(page_rect.height * self.page_scale_factor)
            scroll_width = max(self.canvas_width, int(pil_image.width))
            self.canvas.configure(scrollregion=(0, 0, scroll_width, canvas_height))
            
            print(f"DEBUG: Canvas height: {canvas_height}, Scroll width: {scroll_width}")  # Debug info
            
            # Initialize photo_refs if not exists
            if not hasattr(self, 'photo_refs'):
                self.photo_refs = []
            
            # Render signatures
            self.render_signatures()
            
            print("DEBUG: Page display updated successfully")  # Debug info
            
        except Exception as e:
            print(f"DEBUG: Error in update_page_display: {e}")  # Debug info
            self.show_status(f"Failed to display page: {str(e)}", 5000)
    
    def render_signatures(self):
        """Render signature elements"""
        if not hasattr(self, 'photo_refs'):
            self.photo_refs = []
        
        for element in self.signature_elements:
            if element.page_num == self.current_page:
                self.draw_element_on_canvas(element)
    
    def draw_element_on_canvas(self, element):
        """Draw element on canvas"""
        try:
            # Apply zoom to element position and size
            zoomed_x = element.x * self.zoom_level
            zoomed_y = element.y * self.zoom_level
            zoomed_width = element.width * self.zoom_level
            zoomed_height = element.height * self.zoom_level
            
            if element.element_type == 'image':
                resized_img = element.content.resize(
                    (int(zoomed_width), int(zoomed_height)), 
                    Image.Resampling.LANCZOS
                )
                photo = ImageTk.PhotoImage(resized_img)
                self.photo_refs.append(photo)
                
                element.canvas_id = self.canvas.create_image(
                    zoomed_x, zoomed_y, anchor='nw', image=photo, tags="signature"
                )
                
            elif element.element_type == 'text':
                # Use height as font size for text elements and apply text color
                font_size = max(8, int(zoomed_height - 2))
                text_color = getattr(element, 'text_color', 'black')  # Default to black if no color set
                element.canvas_id = self.canvas.create_text(
                    zoomed_x, zoomed_y, anchor='nw', text=element.content,
                    font=('Arial', font_size), fill=text_color, tags="signature"
                )
        except Exception as e:
            print(f"Error drawing element: {e}")
    
    def add_image_signature(self):
        """Add image signature"""
        if not self.pdf_doc:
            self.show_status("Please open a PDF first", 2000)
            return
        
        file_path = filedialog.askopenfilename(
            title="Select signature image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")]
        )
        
        if file_path:
            try:
                img = Image.open(file_path)
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                # Ask to save
                save_sig = messagebox.askyesno("Save Signature", 
                    "Save this signature for future use?")
                
                if save_sig:
                    sig_name = simpledialog.askstring("Signature Name", 
                        "Enter a name for this signature:")
                    if sig_name:
                        self.save_signature_to_library(img, sig_name)
                        self.update_signature_combo()
                        self.show_status(f"Signature '{sig_name}' saved to library")
                
                # Add to current page
                element = SignatureElement(
                    element_type='image',
                    content=img,
                    x=100, y=100,
                    width=150, height=75,
                    page_num=self.current_page
                )
                
                self.signature_elements.append(element)
                self.draw_element_on_canvas(element)
                self.update_element_list()
                self.show_status("Image signature added")
                
            except Exception as e:
                self.show_status(f"Failed to load image: {str(e)}", 5000)
    
    def add_text_signature(self):
        """Add text element"""
        if not self.pdf_doc:
            self.show_status("Please open a PDF first", 2000)
            return
        
        # Create text element with default font size and black color
        font_size = 12  # Default font size
        
        element = SignatureElement(
            element_type='text',
            content="Text",
            x=100, y=200,
            width=200, height=font_size + 10,
            page_num=self.current_page,
            text_color='black'
        )
        
        self.signature_elements.append(element)
        self.draw_element_on_canvas(element)
        self.update_element_list()
        
        # Auto-select and start editing
        self.selected_element = element
        self.show_selection_border(element)
        
        # Automatically start editing after a short delay
        self.root.after(100, lambda: self.start_text_editing(element))
        self.show_status("Text added - edit text now")
    
    def use_saved_signature(self):
        """Use saved signature"""
        if not self.pdf_doc:
            self.show_status("Please open a PDF first", 2000)
            return
        
        sig_name = self.signature_var.get()
        if not sig_name or sig_name not in self.saved_signatures:
            self.show_status("Please select a saved signature", 2000)
            return
        
        img = self.saved_signatures[sig_name].copy()
        
        element = SignatureElement(
            element_type='image',
            content=img,
            x=100, y=100,
            width=150, height=75,
            page_num=self.current_page
        )
        
        self.signature_elements.append(element)
        self.draw_element_on_canvas(element)
        self.update_element_list()
        self.show_status(f"Used saved signature: {sig_name}")
    
    def update_signature_combo(self):
        """Update signature combobox"""
        signature_names = list(self.saved_signatures.keys())
        self.signature_combo['values'] = signature_names
        if signature_names:
            self.signature_combo.set(signature_names[0])
    
    def delete_signature(self):
        """Delete saved signature"""
        sig_name = self.signature_var.get()
        if not sig_name:
            self.show_status("Please select a signature to delete", 2000)
            return
        
        if messagebox.askyesno("Confirm Delete", f"Delete signature '{sig_name}'?"):
            try:
                # Remove from memory
                if sig_name in self.saved_signatures:
                    del self.saved_signatures[sig_name]
                
                # Remove file
                filename = f"{sig_name}.png"
                img_path = os.path.join(self.signatures_dir, filename)
                if os.path.exists(img_path):
                    os.remove(img_path)
                
                # Update settings
                self.save_settings()
                
                self.update_signature_combo()
                self.show_status(f"Signature '{sig_name}' deleted")
                
            except Exception as e:
                self.show_status(f"Failed to delete signature: {e}", 5000)
    
    def preview_signature(self):
        """Preview signature"""
        sig_name = self.signature_var.get()
        if not sig_name or sig_name not in self.saved_signatures:
            self.show_status("Please select a signature to preview", 2000)
            return
        
        # Create preview window
        preview_window = tk.Toplevel(self.root)
        preview_window.title(f"Preview: {sig_name}")
        preview_window.geometry("400x300")
        
        img = self.saved_signatures[sig_name]
        display_img = img.copy()
        display_img.thumbnail((350, 250), Image.Resampling.LANCZOS)
        
        photo = ImageTk.PhotoImage(display_img)
        label = tk.Label(preview_window, image=photo)
        label.image = photo
        label.pack(expand=True)
        
        self.show_status(f"Previewing signature: {sig_name}")
    
    def change_selected_text_color(self):
        """Change color of selected text element"""
        if not self.selected_element or self.selected_element.element_type != 'text':
            self.show_status("Please select a text element first", 2000)
            return
        
        new_color = self.selected_color_var.get()
        self.selected_element.text_color = new_color
        
        # Redraw element with new color
        if self.selected_element.canvas_id:
            self.canvas.delete(self.selected_element.canvas_id)
        
        self.draw_element_on_canvas(self.selected_element)
        self.show_selection_border(self.selected_element)
        
        self.show_status(f"Text color changed to {new_color}")
    
    def start_text_editing(self, element):
        """Start inline text editing"""
        if element.element_type != 'text':
            return
        
        self.is_editing_text = True
        
        # Hide the original text
        if element.canvas_id:
            self.canvas.delete(element.canvas_id)
        
        # Apply zoom to font size and position
        zoomed_font_size = int((element.height - 2) * self.zoom_level)
        zoomed_x = element.x * self.zoom_level
        zoomed_y = element.y * self.zoom_level
        zoomed_width = element.width * self.zoom_level
        
        # Create entry widget on canvas
        self.text_entry = tk.Entry(self.canvas, font=('Arial', zoomed_font_size))
        self.text_entry.insert(0, element.content)
        self.text_entry.select_range(0, tk.END)
        
        # Position entry widget
        entry_window = self.canvas.create_window(
            zoomed_x, zoomed_y, 
            anchor='nw', 
            window=self.text_entry,
            width=zoomed_width
        )
        
        # Bind events
        self.text_entry.bind('<Return>', lambda e: self.finish_text_editing(element))
        self.text_entry.bind('<Escape>', lambda e: self.cancel_text_editing(element))
        self.text_entry.bind('<FocusOut>', lambda e: self.finish_text_editing(element))
        
        # Focus on entry
        self.text_entry.focus_set()
    
    def finish_text_editing(self, element):
        """Finish text editing and update element"""
        if not self.is_editing_text or not self.text_entry:
            return
        
        # Get new text
        new_text = self.text_entry.get().strip()
        if new_text:
            element.content = new_text
        else:
            # If empty, set a default text
            element.content = "Text"
        
        # Clean up entry widget
        self.text_entry.destroy()
        self.text_entry = None
        self.is_editing_text = False
        
        # Redraw element
        self.draw_element_on_canvas(element)
        self.show_selection_border(element)
        self.update_element_list()
    
    def cancel_text_editing(self, element):
        """Cancel text editing"""
        if not self.is_editing_text or not self.text_entry:
            return
        
        # Clean up entry widget
        self.text_entry.destroy()
        self.text_entry = None
        self.is_editing_text = False
        
        # If element still has placeholder text, give it a proper default
        if element.content == "Click to edit text":
            element.content = "Text"
        
        # Redraw original element
        self.draw_element_on_canvas(element)
        self.show_selection_border(element)
    
    def on_canvas_click(self, event):
        """Handle canvas click"""
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # Clear previous selection visual feedback
        self.canvas.delete("selection_border")
        
        # Find clicked element
        clicked_item = self.canvas.find_closest(canvas_x, canvas_y)[0]
        
        for element in self.signature_elements:
            if element.canvas_id == clicked_item and element.page_num == self.current_page:
                self.selected_element = element
                # Store the zoomed coordinates for dragging
                self.drag_data["x"] = canvas_x
                self.drag_data["y"] = canvas_y
                
                # Update selected color combo if it's a text element
                if element.element_type == 'text':
                    self.selected_color_var.set(getattr(element, 'text_color', 'black'))
                
                # Visual feedback for selected element
                self.show_selection_border(element)
                break
        else:
            self.selected_element = None
    
    def on_double_click(self, event):
        """Handle double click for text editing"""
        if self.selected_element and self.selected_element.element_type == 'text':
            self.start_text_editing(self.selected_element)
    
    def show_selection_border(self, element):
        """Show selection border around selected element"""
        try:
            # Apply zoom to selection border
            zoomed_x = element.x * self.zoom_level
            zoomed_y = element.y * self.zoom_level
            zoomed_width = element.width * self.zoom_level
            zoomed_height = element.height * self.zoom_level
            
            # Create selection border
            border_margin = 5
            self.canvas.create_rectangle(
                zoomed_x - border_margin,
                zoomed_y - border_margin,
                zoomed_x + zoomed_width + border_margin,
                zoomed_y + zoomed_height + border_margin,
                outline='blue',
                width=2,
                dash=(5, 5),
                tags="selection_border"
            )
            
            # Add resize handles
            handle_size = 8
            handles = [
                # Bottom-right corner handle
                (zoomed_x + zoomed_width, zoomed_y + zoomed_height)
            ]
            
            for hx, hy in handles:
                self.canvas.create_rectangle(
                    hx - handle_size//2, hy - handle_size//2,
                    hx + handle_size//2, hy + handle_size//2,
                    fill='blue', outline='darkblue',
                    tags="selection_border"
                )
        except Exception as e:
            print(f"Error showing selection border: {e}")
    
    def on_ctrl_scroll(self, event):
        """Handle Ctrl+Scroll for resizing selected signature"""
        if self.selected_element:
            # Determine scroll direction
            if event.delta > 0:  # Scroll up - increase size
                scale_factor = 1.1
            else:  # Scroll down - decrease size
                scale_factor = 0.9
            
            # Calculate new size
            new_width = max(20, self.selected_element.width * scale_factor)
            new_height = max(10, self.selected_element.height * scale_factor)
            
            # Apply size limits
            new_width = min(500, new_width)
            new_height = min(300, new_height)
            
            # Update element
            self.selected_element.width = new_width
            self.selected_element.height = new_height
            
            # Redraw element
            if self.selected_element.canvas_id:
                self.canvas.delete(self.selected_element.canvas_id)
            self.draw_element_on_canvas(self.selected_element)
            
            # Update selection border
            self.canvas.delete("selection_border")
            self.show_selection_border(self.selected_element)
            
            # Visual feedback (apply zoom to position)
            feedback_x = self.selected_element.x * self.zoom_level + self.selected_element.width * self.zoom_level + 10
            feedback_y = self.selected_element.y * self.zoom_level
            
            self.canvas.create_text(
                feedback_x,
                feedback_y,
                text=f"{int(new_width)}x{int(new_height)}",
                font=('Arial', 10),
                fill='blue',
                tags="size_feedback"
            )
            
            # Remove feedback after 1 second
            self.root.after(1000, lambda: self.canvas.delete("size_feedback"))
    
    def on_scroll(self, event):
        """Handle normal scroll for canvas navigation"""
        if not event.state & 0x4:  # If Ctrl is not pressed
            # Normal canvas scrolling
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def on_canvas_drag(self, event):
        """Handle canvas drag"""
        if self.selected_element:
            canvas_x = self.canvas.canvasx(event.x)
            canvas_y = self.canvas.canvasy(event.y)
            
            delta_x = canvas_x - self.drag_data["x"]
            delta_y = canvas_y - self.drag_data["y"]
            
            # Update element position (account for zoom)
            self.selected_element.x += delta_x / self.zoom_level
            self.selected_element.y += delta_y / self.zoom_level
            
            # Move the canvas item
            self.canvas.move(self.selected_element.canvas_id, delta_x, delta_y)
            
            # Update selection border
            self.canvas.delete("selection_border")
            self.show_selection_border(self.selected_element)
            
            self.drag_data["x"] = canvas_x
            self.drag_data["y"] = canvas_y
    
    def on_canvas_release(self, event):
        """Handle canvas release"""
        pass
    
    def prev_page(self):
        """Previous page"""
        if self.pdf_doc and self.current_page > 0:
            self.current_page -= 1
            self.update_page_display()
            self.selected_element = None
    
    def next_page(self):
        """Next page"""
        if self.pdf_doc and self.current_page < len(self.pdf_doc) - 1:
            self.current_page += 1
            self.update_page_display()
            self.selected_element = None
    
    def delete_selected(self):
        """Delete selected element"""
        if self.selected_element:
            if self.selected_element.canvas_id:
                self.canvas.delete(self.selected_element.canvas_id)
            
            self.signature_elements.remove(self.selected_element)
            self.selected_element = None
            self.update_element_list()
    
    def clear_all(self):
        """Clear all elements"""
        if messagebox.askyesno("Confirm", "Delete all signature elements?"):
            self.signature_elements.clear()
            self.selected_element = None
            self.update_page_display()
            self.update_element_list()
    
    def update_element_list(self):
        """Update element list"""
        self.element_listbox.delete(0, tk.END)
        for i, element in enumerate(self.signature_elements):
            content_preview = element.content if element.element_type == 'text' else 'Image'
            self.element_listbox.insert(tk.END, 
                f"Page {element.page_num + 1}: {element.element_type.title()} - {content_preview}")
    
    def on_element_select(self, event):
        """Handle element selection"""
        selection = self.element_listbox.curselection()
        if selection:
            index = selection[0]
            if index < len(self.signature_elements):
                element = self.signature_elements[index]
                
                if element.page_num != self.current_page:
                    self.current_page = element.page_num
                    self.update_page_display()
                
                self.selected_element = element
    
    def save_pdf(self):
        """Save PDF with signatures (auto-save with _signed suffix)"""
        if not self.pdf_doc:
            self.show_status("No PDF loaded", 2000)
            return
        
        if not self.signature_elements:
            self.show_status("No signatures to save", 2000)
            return
        
        try:
            self.show_status("Saving PDF with signatures...")
            
            # Generate output filename automatically
            original_path = self.pdf_file_path
            file_dir = os.path.dirname(original_path)
            file_name = os.path.splitext(os.path.basename(original_path))[0]
            
            # Create safe filename from signature name (remove special characters)
            safe_name = "".join(c for c in self.signature_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name.replace(' ', '_')
            
            output_filename = f"{file_name}_signed_by_{safe_name}.pdf"
            output_path = os.path.join(file_dir, output_filename)
            
            # Create a copy of the original document
            doc_copy = fitz.open(self.pdf_file_path)
            pages_with_signatures = set()
            
            for page_num in range(len(doc_copy)):
                page = doc_copy[page_num]
                page_elements = [elem for elem in self.signature_elements if elem.page_num == page_num]
                
                # Track pages with image signatures only
                has_image_signature = any(elem.element_type == 'image' for elem in page_elements)
                
                # Add signature elements to page
                for element in page_elements:
                    if element.element_type == 'image':
                        # Optimize image before inserting
                        img_bytes = io.BytesIO()
                        
                        # Resize image if too large to reduce file size
                        img_copy = element.content.copy()
                        max_size = (800, 600)  # Maximum dimensions
                        img_copy.thumbnail(max_size, Image.Resampling.LANCZOS)
                        
                        # Save with optimization
                        img_copy.save(img_bytes, format='PNG', optimize=True, compress_level=9)
                        img_bytes.seek(0)
                        
                        rect = fitz.Rect(
                            element.x / self.base_scale_factor,
                            element.y / self.base_scale_factor,
                            (element.x + element.width) / self.base_scale_factor,
                            (element.y + element.height) / self.base_scale_factor
                        )
                        
                        page.insert_image(rect, stream=img_bytes.getvalue())
                        
                    elif element.element_type == 'text':
                        point = fitz.Point(
                            element.x / self.base_scale_factor, 
                            (element.y + element.height) / self.base_scale_factor
                        )
                        font_size = max(8, element.height / self.base_scale_factor)
                        
                        # Convert text color to RGB tuple for PyMuPDF
                        text_color = getattr(element, 'text_color', 'black')
                        color_map = {
                            'black': (0, 0, 0),
                            'red': (1, 0, 0),
                            'blue': (0, 0, 1),
                            'green': (0, 0.5, 0),
                            'purple': (0.5, 0, 0.5),
                            'orange': (1, 0.5, 0),
                            'brown': (0.6, 0.3, 0),
                            'gray': (0.5, 0.5, 0.5)
                        }
                        rgb_color = color_map.get(text_color, (0, 0, 0))  # Default to black
                        
                        try:
                            page.insert_text(point, element.content, 
                                           fontsize=font_size, color=rgb_color)
                        except Exception as font_error:
                            print(f"Font error, using fallback: {font_error}")
                            page.insert_text(point, element.content, 
                                           fontsize=font_size, color=rgb_color, 
                                           fontname="helv")
                
                # Only add signature info for pages with image signatures
                if has_image_signature:
                    pages_with_signatures.add(page_num)
            
            # Add signature info text only for image signatures
            signature_info_text = f"Signed by {self.signature_name}\n{datetime.now().strftime('%b %d, %Y %H:%M:%S')}"
            for page_num in pages_with_signatures:
                page = doc_copy[page_num]
                page_elements = [elem for elem in self.signature_elements 
                               if elem.page_num == page_num and elem.element_type == 'image']
                
                for element in page_elements:
                    text_point = fitz.Point(
                        element.x / self.base_scale_factor,
                        element.y / self.base_scale_factor
                    )
                    
                    try:
                        page.insert_text(text_point, signature_info_text, 
                                       fontsize=6, color=(0.4, 0.4, 0.4))
                        break  # Only add once per page
                    except Exception as e:
                        try:
                            page.insert_text(text_point, signature_info_text)
                            break
                        except:
                            pass
            
            # Save with optimization settings
            doc_copy.save(output_path, 
                         garbage=4,      # Remove unused objects
                         deflate=True,   # Compress streams
                         clean=True)     # Clean up document
            doc_copy.close()
            
            success_msg = f"PDF saved as: {output_filename}"
            if pages_with_signatures:
                success_msg += f" ({len(pages_with_signatures)} pages signed)"
            
            self.show_status(success_msg, 4000)
            
        except Exception as e:
            print(f"Save error: {e}")
            self.show_status(f"Failed to save PDF: {str(e)}", 5000)

def main():
    root = tk.Tk()
    app = PDFSignatureApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()