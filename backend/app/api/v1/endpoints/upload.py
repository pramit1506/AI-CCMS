from io import BytesIO
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from app.shared.responses import APIResponse

router = APIRouter()

@router.post("/extract-text")
async def extract_text(file: UploadFile = File(...)):
    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    filename = file.filename or "uploaded-file"
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    try:
        if extension == "pdf":
            from pypdf import PdfReader

            reader = PdfReader(BytesIO(content))
            text = "\n".join(page.extract_text() or "" for page in reader.pages).strip()
        elif extension == "docx":
            from docx import Document

            document = Document(BytesIO(content))
            text = "\n".join(paragraph.text for paragraph in document.paragraphs).strip()
        elif extension in {"txt", "eml"}:
            text = content.decode("utf-8", errors="ignore").strip()
        else:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Unsupported file type. Please upload PDF, DOCX, TXT, or EML.",
            )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not extract text from {filename}: {exc}",
        ) from exc

    if not text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No readable text was found in the uploaded file.",
        )
    
    return APIResponse(
        success=True, 
        message="Text extracted", 
        data={"text": text, "filename": filename}
    )
