FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir PyMuPDF faiss-cpu langchain==0.1.19 chromadb google-generativeai==0.4.1 langchain-google-genai==1.0.1 langchain-community==0.0.38 flask

# Make port 80 available to the world outside this container 
EXPOSE 80

# Define environment variable
ENV GOOGLE_API_KEY=\${GOOGLE_API_KEY}

# Run app.py when the container launches
CMD ["python", "app.py"]