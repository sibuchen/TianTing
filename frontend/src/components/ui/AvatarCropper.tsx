'use client';

import React, { useState, useCallback } from 'react';
import Cropper from 'react-easy-crop';
import type { Area } from 'react-easy-crop';

interface AvatarCropperProps {
  image: string;
  visible: boolean;
  onConfirm: (blob: Blob) => void;
  onCancel: () => void;
}

const createImage = (url: string): Promise<HTMLImageElement> =>
  new Promise((resolve, reject) => {
    const image = new Image();
    image.addEventListener('load', () => resolve(image));
    image.addEventListener('error', (error) => reject(error));
    image.setAttribute('crossOrigin', 'anonymous');
    image.src = url;
  });

function getCroppedImg(imageSrc: string, pixelCrop: Area): Promise<Blob> {
  return new Promise(async (resolve, reject) => {
    const image = await createImage(imageSrc);
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    if (!ctx) {
      reject(new Error('No 2d context'));
      return;
    }

    const size = Math.min(pixelCrop.width, pixelCrop.height, 400);
    canvas.width = size;
    canvas.height = size;

    ctx.drawImage(
      image,
      pixelCrop.x,
      pixelCrop.y,
      pixelCrop.width,
      pixelCrop.height,
      0,
      0,
      size,
      size
    );

    canvas.toBlob(
      (blob) => {
        if (!blob) {
          reject(new Error('Canvas is empty'));
          return;
        }
        resolve(blob);
      },
      'image/jpeg',
      0.9
    );
  });
}

export default function AvatarCropper({ image, visible, onConfirm, onCancel }: AvatarCropperProps) {
  const [crop, setCrop] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1);
  const [croppedAreaPixels, setCroppedAreaPixels] = useState<Area | null>(null);
  const [loading, setLoading] = useState(false);

  const onCropComplete = useCallback((_: Area, croppedAreaPixels: Area) => {
    setCroppedAreaPixels(croppedAreaPixels);
  }, []);

  const handleConfirm = async () => {
    if (!croppedAreaPixels) return;
    setLoading(true);
    try {
      const blob = await getCroppedImg(image, croppedAreaPixels);
      onConfirm(blob);
    } catch {
      onCancel();
    } finally {
      setLoading(false);
    }
  };

  if (!visible) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-card-bg rounded-xl shadow-lg w-[520px] max-w-[95vw] overflow-hidden">
        <div className="px-lg py-md border-b border-border flex items-center justify-between">
          <h3 className="text-lg font-semibold text-on-surface">裁剪头像</h3>
          <button
            onClick={onCancel}
            className="text-on-surface-variant hover:text-on-surface transition-colors"
          >
            <span className="material-symbols-outlined">close</span>
          </button>
        </div>
        <div className="relative w-full" style={{ height: 360 }}>
          <Cropper
            image={image}
            crop={crop}
            zoom={zoom}
            aspect={1}
            cropShape="round"
            showGrid={false}
            onCropChange={setCrop}
            onCropComplete={onCropComplete}
            onZoomChange={setZoom}
          />
        </div>
        <div className="px-lg py-sm flex items-center gap-md">
          <span className="material-symbols-outlined text-on-surface-variant text-sm">zoom_out</span>
          <input
            type="range"
            min={1}
            max={3}
            step={0.01}
            value={zoom}
            onChange={(e) => setZoom(Number(e.target.value))}
            className="flex-1 h-1 accent-primary cursor-pointer"
          />
          <span className="material-symbols-outlined text-on-surface-variant">zoom_in</span>
        </div>
        <div className="px-lg py-md border-t border-border flex justify-end gap-md">
          <button
            onClick={onCancel}
            className="px-lg py-sm rounded-lg border border-outline-variant text-on-surface-variant hover:bg-surface-bg transition-colors font-label-md text-label-md"
          >
            取消
          </button>
          <button
            onClick={handleConfirm}
            disabled={loading}
            className="px-lg py-sm rounded-lg bg-primary text-on-primary hover:bg-primary-container transition-colors font-label-md text-label-md disabled:opacity-50"
          >
            {loading ? '处理中...' : '确认'}
          </button>
        </div>
      </div>
    </div>
  );
}