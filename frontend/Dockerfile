# frontend/Dockerfile — multi-stage: build the SPA, then serve it with nginx
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
# Vite reads VITE_* from the environment at build time. Pass them as build args.
ARG VITE_API_BASE_URL=/api/v1
ARG VITE_MB_DASHBOARD_RESULTS_PHYSICAL
ARG VITE_MB_DASHBOARD_RESULTS_FRAMEWORK
ARG VITE_MB_DASHBOARD_FINANCE_CATEGORY
ARG VITE_MB_DASHBOARD_FINANCE_COMPONENT
ARG VITE_MB_DASHBOARD_PROCUREMENT
ARG VITE_MB_DASHBOARD_GRIEVANCES
ARG VITE_MB_DASHBOARD_IMPACT
ARG VITE_MB_DASHBOARD_ACTIVITIES
RUN npm run build

FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 8080
