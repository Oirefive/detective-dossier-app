import { useEffect, useMemo, useState } from "react";

type PhotoUploadFieldProps = {
  label: string;
  value: string | null;
  onUpload: (file: File) => void | Promise<void>;
  onClear: () => void;
  uploading?: boolean;
  compact?: boolean;
};

export function PhotoUploadField({
  label,
  value,
  onUpload,
  onClear,
  uploading = false,
  compact = false,
}: PhotoUploadFieldProps) {
  const [cacheKey, setCacheKey] = useState(0);

  useEffect(() => {
    setCacheKey((current) => current + 1);
  }, [value]);

  const imageSrc = useMemo(() => {
    if (!value) return null;
    const divider = value.includes("?") ? "&" : "?";
    return `${value}${divider}v=${cacheKey}`;
  }, [cacheKey, value]);

  return (
    <div className={`photo-upload ${compact ? "photo-upload--compact" : ""}`}>
      <div className="photo-upload__preview">
        {imageSrc ? (
          <>
            <img src={imageSrc} alt={label} className="photo-upload__image" />
            <div className="photo-upload__overlay">
              <label className="button-like ghost photo-upload__button">
                <input
                  type="file"
                  accept="image/png,image/jpeg,image/webp"
                  onChange={(event) => {
                    const file = event.target.files?.[0];
                    if (file) void onUpload(file);
                    event.currentTarget.value = "";
                  }}
                />
                {uploading ? "Загрузка..." : "Изменить"}
              </label>
              <button type="button" className="ghost photo-upload__icon" onClick={onClear} disabled={uploading}>
                ×
              </button>
            </div>
          </>
        ) : (
          <label className="photo-upload__empty">
            <input
              type="file"
              accept="image/png,image/jpeg,image/webp"
              onChange={(event) => {
                const file = event.target.files?.[0];
                if (file) void onUpload(file);
                event.currentTarget.value = "";
              }}
            />
            <strong>{uploading ? "Загрузка..." : "Добавить фото"}</strong>
            <span>{label}</span>
          </label>
        )}
      </div>
    </div>
  );
}
