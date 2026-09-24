import { defineRailway, github, project, service, volume } from "railway/iac";

export default defineRailway(() => {
  const data = volume("pennywise-data", { sizeMB: 1024 });

  const api = service("pennywise-api", {
    source: github("minhahamin/PennyWise", {
      branch: "main",
      rootDirectory: "backend",
    }),
    healthcheck: "/health",
    volumeMounts: {
      "/data": data,
    },
    env: {
      DATABASE_URL: "sqlite:////data/pennywise.db",
      UPLOAD_DIR: "/data/uploads",
      CORS_ORIGINS: "*",
    },
  });

  // NOTE: VITE_API_BASE는 백엔드 공개 도메인 발급 후 실제 URL로 교체한다.
  // (Vite는 빌드 타임에 주입되므로 변수 변경 시 프론트엔드가 자동 리빌드된다.)
  const web = service("pennyWise", {
    source: github("minhahamin/PennyWise", {
      branch: "main",
      rootDirectory: "frontend",
    }),
    env: {
      VITE_API_BASE: "https://pennywise-api-production.up.railway.app",
    },
  });

  return project("pennyWise", {
    resources: [api, data, web],
  });
});
