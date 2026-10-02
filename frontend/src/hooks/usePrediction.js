import { useState, useCallback, useEffect } from 'react';
import { predictCrop } from '../services/api';

/**
 * Pipeline stages shown during live prediction.
 */
export const ANALYSIS_STAGES = [
  { id: 'validation', label: 'Image validation & hashing' },
  { id: 'health', label: 'Health classification (EfficientNet-B0)' },
  { id: 'disease', label: 'Disease prediction (PlantWild v2 - 115 classes)' },
  { id: 'explainability', label: 'Grad-CAM visual activation generation' },
  { id: 'segmentation', label: 'U-Net lesion segmentation' },
  { id: 'severity', label: 'Quantitative severity estimation' },
  { id: 'traceability', label: 'Cryptographic evidence recording' },
];

export function usePrediction(initialResult = null, initialImageSrc = null) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(initialImageSrc || null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [currentStageIndex, setCurrentStageIndex] = useState(0);
  const [result, setResult] = useState(initialResult || null);
  const [error, setError] = useState(null);

  // Manage object URL lifecycle to prevent memory leaks
  const handleSelectFile = useCallback((file) => {
    if (previewUrl && typeof previewUrl === 'string' && previewUrl.startsWith('blob:')) {
      URL.revokeObjectURL(previewUrl);
    }
    if (!file) {
      setSelectedFile(null);
      setPreviewUrl(null);
      return;
    }
    setSelectedFile(file);
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    setError(null);
  }, [previewUrl]);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      if (previewUrl && typeof previewUrl === 'string' && previewUrl.startsWith('blob:')) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  const runAnalysis = useCallback(async (fileToAnalyze = null) => {
    const file = fileToAnalyze || selectedFile;
    if (!file) {
      setError('Please choose a leaf image file first.');
      return null;
    }

    setIsAnalyzing(true);
    setError(null);
    setCurrentStageIndex(0);

    // Subtle stage progression interval while awaiting the API response
    const stageTimer = setInterval(() => {
      setCurrentStageIndex((prev) => {
        if (prev < ANALYSIS_STAGES.length - 1) {
          return prev + 1;
        }
        return prev;
      });
    }, 900);

    try {
      const data = await predictCrop(file);
      clearInterval(stageTimer);
      setCurrentStageIndex(ANALYSIS_STAGES.length - 1);
      setResult(data);
      return data;
    } catch (err) {
      clearInterval(stageTimer);
      setError(err.message || 'An error occurred during prediction.');
      return null;
    } finally {
      setIsAnalyzing(false);
    }
  }, [selectedFile]);

  const reset = useCallback(() => {
    if (previewUrl && typeof previewUrl === 'string' && previewUrl.startsWith('blob:')) {
      URL.revokeObjectURL(previewUrl);
    }
    setSelectedFile(null);
    setPreviewUrl(null);
    setResult(null);
    setError(null);
    setIsAnalyzing(false);
    setCurrentStageIndex(0);
  }, [previewUrl]);

  return {
    selectedFile,
    previewUrl,
    isAnalyzing,
    currentStageIndex,
    stages: ANALYSIS_STAGES,
    result,
    error,
    selectFile: handleSelectFile,
    runAnalysis,
    reset,
  };
}
