FROM node:20-alpine

WORKDIR /app

COPY apps/public-web/package*.json /app/
RUN npm install

COPY apps/public-web /app

ARG VITE_AFRITECH_PUBLIC_API_URL=
ENV VITE_AFRITECH_PUBLIC_API_URL=${VITE_AFRITECH_PUBLIC_API_URL}

RUN npm run build

EXPOSE 4175

CMD ["npx", "vite", "preview", "--host", "0.0.0.0", "--port", "4175"]

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD wget --spider -q http://127.0.0.1:4175/ || exit 1
