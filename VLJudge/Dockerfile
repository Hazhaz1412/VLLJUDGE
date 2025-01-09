FROM python:3.9

WORKDIR /app

# Sao chép toàn bộ mã nguồn của bạn vào thư mục /app trong container
COPY . /app

# Cài đặt các thư viện phụ thuộc
RUN apt-get update && apt-get install -y g++ && pip install psutil

COPY hidden_testcases /app/hidden_testcases
RUN chmod -R 755 /app/hidden_testcases


CMD ["python3", "judge.py"]
