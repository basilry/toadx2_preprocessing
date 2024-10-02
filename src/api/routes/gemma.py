import os
import torch
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForCausalLM, Trainer, TrainingArguments
from fastapi import APIRouter, HTTPException
from dotenv import load_dotenv

load_dotenv()
huggingfaceToken = os.getenv('HUGGINGFACE_TOKEN')

router = APIRouter()

model_name = "basilry/gemma2-2-2b-it-fine-tuned-korean-model"
tokenizer = AutoTokenizer.from_pretrained(model_name, use_auth_token=huggingfaceToken)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    attn_implementation='eager',
    torch_dtype=torch.float16,  # 혼합 정밀도 사용
    device_map='auto',
    use_auth_token=huggingfaceToken
)

model.eval()

# GPU 사용 설정
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

class ChatRequest(BaseModel):
    user_input: str

def generate_response(input_text):
    # 입력 토큰화
    inputs = tokenizer(
        input_text,
        return_tensors="pt",
        max_length=128,
        truncation=True,
    ).to(device)

    # 모델을 사용하여 응답 생성
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_length=128,
            num_beams=5,
            early_stopping=True,
        )

    # 출력 디코딩
    generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

    return generated_text


# 한국어로 대화
@router.post("/chat")
async def chat(request: ChatRequest):
    # Check Tokenizer
    response = tokenizer.tokenize("안녕하세요, 오늘 날씨는 어떻습니까?")
    # user_input = request.user_input
    # if user_input.lower() in ["exit", "quit", "종료"]:
    #     raise HTTPException(status_code=400, detail="대화 종료 명령어는 허용되지 않습니다.")
    #
    # input_text = f"사용자: {user_input}\nAI:"
    # response = generate_response(input_text)
    #
    # # 응답에서 'AI:' 부분 추출
    # response = response.split("AI:")[-1].strip()

    return {"response": response}