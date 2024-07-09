# Use the official Nginx image as the base image
FROM nginx:1.27.0

# Copy the custom nginx configuration file into the container
COPY ./nginx.conf /etc/nginx/nginx.conf

# Create a directory for server cache and set the appropriate permissions
RUN mkdir -p /server_cache && chmod 777 /server_cache

# Expose port 80 to the host
EXPOSE 80

# Start Nginx when the container launches
CMD ["nginx", "-g", "daemon off;"]