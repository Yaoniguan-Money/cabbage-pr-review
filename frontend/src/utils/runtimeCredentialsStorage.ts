const STORAGE_KEY = "pr-review-runtime-credentials-v1";

export type StoredRuntimeCredentials = {
  enable_cloud: boolean;
  enable_github: boolean;
  cloud_api_base: string;
  cloud_api_key: string;
  cloud_flash_model: string;
  cloud_pro_model: string;
  github_token: string;
};

const EMPTY: StoredRuntimeCredentials = {
  enable_cloud: false,
  enable_github: false,
  cloud_api_base: "",
  cloud_api_key: "",
  cloud_flash_model: "",
  cloud_pro_model: "",
  github_token: "",
};

function normalize(parsed: Partial<StoredRuntimeCredentials>): StoredRuntimeCredentials {
  const cloudKey = parsed.cloud_api_key?.trim() ?? "";
  const gh = parsed.github_token?.trim() ?? "";
  return {
    enable_cloud: parsed.enable_cloud ?? Boolean(cloudKey),
    enable_github: parsed.enable_github ?? Boolean(gh),
    cloud_api_base: parsed.cloud_api_base ?? "",
    cloud_api_key: parsed.cloud_api_key ?? "",
    cloud_flash_model: parsed.cloud_flash_model ?? "",
    cloud_pro_model: parsed.cloud_pro_model ?? "",
    github_token: parsed.github_token ?? "",
  };
}

export function loadRuntimeCredentials(): StoredRuntimeCredentials {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { ...EMPTY };
    const parsed = JSON.parse(raw) as Partial<StoredRuntimeCredentials>;
    return normalize(parsed);
  } catch {
    return { ...EMPTY };
  }
}

export function saveRuntimeCredentials(creds: StoredRuntimeCredentials): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(creds));
}

export function clearRuntimeCredentials(): void {
  localStorage.removeItem(STORAGE_KEY);
}

export function hasRuntimeCloudKey(creds: StoredRuntimeCredentials): boolean {
  return Boolean(creds.cloud_api_key.trim());
}

export function isCloudCredentialsEnabled(creds: StoredRuntimeCredentials): boolean {
  return creds.enable_cloud && hasRuntimeCloudKey(creds);
}

export function isGithubCredentialsEnabled(creds: StoredRuntimeCredentials): boolean {
  return creds.enable_github && Boolean(creds.github_token.trim());
}

export function toApiPayload(creds: StoredRuntimeCredentials) {
  const cloud = isCloudCredentialsEnabled(creds);
  const gh = isGithubCredentialsEnabled(creds);
  if (!cloud && !gh) {
    return undefined;
  }
  return {
    cloud_api_base: cloud ? creds.cloud_api_base.trim() || undefined : undefined,
    cloud_api_key: cloud ? creds.cloud_api_key.trim() || undefined : undefined,
    cloud_flash_model: cloud ? creds.cloud_flash_model.trim() || undefined : undefined,
    cloud_pro_model: cloud ? creds.cloud_pro_model.trim() || undefined : undefined,
    github_token: gh ? creds.github_token.trim() : undefined,
  };
}
