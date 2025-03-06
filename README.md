# Quick PDF Editor

## 📖 Description

This project was originally developed for personal use, but it is now shared online for others who may find it useful. It is primarily designed for editing PDF files, such as modifying the table of contents. 

More features will be added as needed in future updates.

## 🚀 Features

- Edit and modify PDF table of contents  
- (Upcoming features will be added as needed)

## ▶️ Getting Started

### Prerequisites
- Ensure you have `Python` and `make` installed on your system.
- Download this repo and save it to your local folder

### Steps
```bash
# Install dependencies
make install

# Run the application
python ./main.py --help

# (Optional) Build the application as an executable and run it from the executable
make build & ./dist/main --help
```

## 🛠 Usage

### Example 1: Update Table of Contents
 
To get started, create a file called `data.json` and use the following example JSON structure. This data represents a list of contents, each with an `title`, `page_num`, and `child_nodes`.

```json
[
  {
    "page_num": 1,
    "title": "Cover",
    "child_nodes": null
  },
  {
    "page_num": 5,
    "title": "Contents",
    "child_nodes": [
      {
        "page_num": 5,
        "title": "Chapter 1",
        "child_nodes": null
      },
      {
        "page_num": 6,
        "title": "Chapter 2",
        "child_nodes": null
      }
    ]
  }
]
```

Update a PDF file with a Table of Contents
```bash
python ./main.py UPDATE-CONTENT  -f "your-pdf-input-path" -c "./data.json" -o "new-pdf-output-path"
```

### Example 2: Export Table of Contents
```bash
python ./main.py EXPORT-CONTENT  -f "your-pdf-input-path" -o "table-of-contents-json-output-path"
```

## 📜 License

I have not decided which license to use for this project yet. Please feel free to check back later for updates on licensing.


## 🤝 Contributing

Since this is a personal project, I am not actively seeking contributions. However, if you would like to make any changes or improvements, please feel free to fork the repository and make changes in your own version.

This project is updated by me as needed, so any contributions from your side will not be directly merged unless specifically requested by me. Thank you for understanding!
