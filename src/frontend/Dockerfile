# Use Node base image
FROM node:18-slim

WORKDIR /app

# Copy package files and install
COPY package*.json ./
RUN npm install

# Copy the rest of the frontend code
COPY . .

# Adding the port flag ensures it matches your docker-compose
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]
