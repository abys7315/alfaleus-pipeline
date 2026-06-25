FROM node:20-alpine as build

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Build the React app via Vite
# This reads the environment variables provided by Railway at build time
RUN npm run build

# Serve using a lightweight static web server
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html

# Copy a basic nginx conf to handle SPA routing
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose default Nginx port (or use PORT if Railway overrides, but Nginx is 80)
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
