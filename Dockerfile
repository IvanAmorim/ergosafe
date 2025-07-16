FROM python:3.11-slim

# Instalar dependências do sistema para OpenCV + GStreamer
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    cmake \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev \
    gstreamer1.0-tools \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Variáveis
ENV OPENCV_VER=74

# Diretório temporário
WORKDIR /tmp

# Clonar e construir OpenCV com GStreamer ativado
RUN git clone --branch ${OPENCV_VER} --depth 1 --recurse-submodules --shallow-submodules https://github.com/opencv/opencv-python.git opencv-python \
    && cd opencv-python \
    && export ENABLE_CONTRIB=0 \
    && export ENABLE_HEADLESS=1 \
    && export CMAKE_ARGS="-DWITH_GSTREAMER=ON" \
    && python3 -m pip install --upgrade pip setuptools wheel \
    && python3 -m pip wheel . --verbose \
    && python3 -m pip install opencv_python*.whl \
    && cd / && rm -rf /tmp/*

# Definir diretório de trabalho
WORKDIR /code

# Copiar requirements
COPY requirements.txt .

# Instalar dependências do projeto
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código-fonte
COPY ./common ./common

# Comando por defeito (pode ser alterado via docker-compose)
CMD ["uvicorn", "gateway:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
