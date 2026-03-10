import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { HelpCircle, X, ChevronLeft, ChevronRight } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export default function FeatureTips({ feature, className = "" }) {
  const [tips, setTips] = useState([]);
  const [currentTip, setCurrentTip] = useState(0);
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    if (isOpen && tips.length === 0) {
      fetchTips();
    }
  }, [isOpen, feature]);

  const fetchTips = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/onboarding/tips/${feature}`, {
        withCredentials: true
      });
      setTips(response.data.tips || []);
    } catch (err) {
      console.error('Error fetching tips:', err);
    }
  };

  const nextTip = () => {
    setCurrentTip((prev) => (prev + 1) % tips.length);
  };

  const prevTip = () => {
    setCurrentTip((prev) => (prev - 1 + tips.length) % tips.length);
  };

  if (tips.length === 0 && !isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className={`p-1.5 rounded-full hover:bg-slate-100 transition-colors ${className}`}
        title="Astuces"
      >
        <HelpCircle className="w-4 h-4 text-slate-400" />
      </button>
    );
  }

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`p-1.5 rounded-full hover:bg-slate-100 transition-colors ${className}`}
        title="Astuces"
      >
        <HelpCircle className="w-4 h-4 text-slate-400" />
      </button>

      {isOpen && tips.length > 0 && (
        <div className="absolute right-0 top-full mt-2 w-72 bg-white rounded-xl shadow-xl border border-slate-200 p-4 z-50">
          <div className="flex items-start justify-between mb-2">
            <span className="text-xs font-semibold text-violet-600 uppercase">
              Astuce {currentTip + 1}/{tips.length}
            </span>
            <button 
              onClick={() => setIsOpen(false)}
              className="text-slate-400 hover:text-slate-600"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <p className="text-sm text-slate-700 mb-4">
            {tips[currentTip]}
          </p>

          {tips.length > 1 && (
            <div className="flex items-center justify-between">
              <button
                onClick={prevTip}
                className="p-1 rounded hover:bg-slate-100 transition-colors"
              >
                <ChevronLeft className="w-4 h-4 text-slate-600" />
              </button>
              
              <div className="flex gap-1">
                {tips.map((_, i) => (
                  <div
                    key={i}
                    className={`w-1.5 h-1.5 rounded-full ${
                      i === currentTip ? 'bg-violet-500' : 'bg-slate-300'
                    }`}
                  />
                ))}
              </div>

              <button
                onClick={nextTip}
                className="p-1 rounded hover:bg-slate-100 transition-colors"
              >
                <ChevronRight className="w-4 h-4 text-slate-600" />
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
