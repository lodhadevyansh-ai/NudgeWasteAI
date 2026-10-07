import { useState, useRef } from 'react';
import { Upload, X, Sparkles, Loader2 } from 'lucide-react';
import { Card } from '../common/Card';

export const ImageUploader = ({ onAnalyze, isLoading }) => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [itemHint, setItemHint] = useState('');
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      processFile(file);
    }
  };

  const processFile = (file) => {
    setSelectedFile(file);
    const reader = new FileReader();
    reader.onloadend = () => {
      setImagePreview(reader.result);
    };
    reader.readAsDataURL(file);
  };

  const handleClear = () => {
    setSelectedFile(null);
    setImagePreview(null);
    setItemHint('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!selectedFile && !itemHint.trim()) return;

    onAnalyze({
      file: selectedFile,
      itemLabel: itemHint.trim(),
    });
  };

  return (
    <Card className="max-w-2xl mx-auto">
      <form onSubmit={handleSubmit} className="space-y-5">
        <div>
          <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-1">
            Scan & Classify Waste Item
          </h3>
          <p className="text-xs md:text-sm text-slate-500 dark:text-slate-400">
            Upload or capture an image of your waste item for AI-powered statutory classification.
          </p>
        </div>

        {/* Dropzone / Preview Area */}
        {!imagePreview ? (
          <div
            onClick={() => fileInputRef.current?.click()}
            className="border-2 border-dashed border-slate-300 dark:border-slate-700 hover:border-emerald-500 dark:hover:border-emerald-500 rounded-2xl p-8 text-center cursor-pointer transition-all bg-slate-50/50 dark:bg-slate-900/40 group flex flex-col items-center justify-center min-h-[220px]"
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept="image/*"
              className="hidden"
            />
            <div className="w-14 h-14 rounded-2xl bg-emerald-100 dark:bg-emerald-950/80 text-emerald-600 dark:text-emerald-400 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
              <Upload className="w-7 h-7" />
            </div>
            <p className="text-sm font-bold text-slate-800 dark:text-slate-200">
              Click to upload or drag image here
            </p>
            <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">
              Supports PNG, JPG, JPEG, WEBP files
            </p>
          </div>
        ) : (
          <div className="relative rounded-2xl overflow-hidden border border-slate-200 dark:border-slate-800 bg-black flex items-center justify-center max-h-[360px]">
            <img
              src={imagePreview}
              alt="Uploaded waste preview"
              className="object-contain max-h-[360px] w-full"
            />
            <button
              type="button"
              onClick={handleClear}
              className="absolute top-3 right-3 p-1.5 rounded-full bg-slate-900/80 text-white hover:bg-red-600 transition-colors"
              title="Remove image"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Item Name / Hint Input */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
            Item Name / Label Hint (Optional)
          </label>
          <input
            type="text"
            value={itemHint}
            onChange={(e) => setItemHint(e.target.value)}
            placeholder="e.g. Plastic bottle, Banana peel, Battery, Newspaper"
            className="w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
          />
        </div>

        {/* Analyze Button */}
        <button
          type="submit"
          disabled={isLoading || (!selectedFile && !itemHint.trim())}
          className="w-full flex items-center justify-center gap-2 py-3 px-6 rounded-xl bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold text-sm shadow-md shadow-emerald-600/20 transition-all"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Analyzing Waste Item...</span>
            </>
          ) : (
            <>
              <Sparkles className="w-5 h-5" />
              <span>Classify Waste with AI</span>
            </>
          )}
        </button>
      </form>
    </Card>
  );
};
