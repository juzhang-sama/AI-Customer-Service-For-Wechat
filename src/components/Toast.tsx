import React, { useEffect, useState } from 'react';
import { CheckCircle, XCircle, X } from 'lucide-react';

export interface ToastMessage {
    id: string;
    type: 'success' | 'error';
    message: string;
}

interface ToastProps {
    toast: ToastMessage;
    onClose: (id: string) => void;
}

const Toast: React.FC<ToastProps> = ({ toast, onClose }) => {
    useEffect(() => {
        const timer = setTimeout(() => {
            onClose(toast.id);
        }, 5000);
        return () => clearTimeout(timer);
    }, [toast.id, onClose]);

    return (
        <div
            className={`flex items-center space-x-3 p-4 rounded-xl shadow-lg border backdrop-blur-md animate-in slide-in-from-right duration-300 ${
                toast.type === 'success'
                    ? 'bg-green-50/90 border-green-200 text-green-800'
                    : 'bg-red-50/90 border-red-200 text-red-800'
            }`}
        >
            {toast.type === 'success' ? (
                <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0" />
            ) : (
                <XCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
            )}
            <span className="text-sm font-medium flex-1">{toast.message}</span>
            <button
                onClick={() => onClose(toast.id)}
                className="p-1 hover:bg-black/5 rounded-lg transition-colors"
            >
                <X className="w-4 h-4" />
            </button>
        </div>
    );
};

interface ToastContainerProps {
    toasts: ToastMessage[];
    onClose: (id: string) => void;
}

export const ToastContainer: React.FC<ToastContainerProps> = ({ toasts, onClose }) => {
    if (toasts.length === 0) return null;

    return (
        <div className="fixed top-4 right-4 z-50 space-y-2 max-w-sm">
            {toasts.map((toast) => (
                <Toast key={toast.id} toast={toast} onClose={onClose} />
            ))}
        </div>
    );
};

// Hook for managing toasts
export const useToast = () => {
    const [toasts, setToasts] = useState<ToastMessage[]>([]);

    const showToast = (message: string, type: 'success' | 'error' = 'success') => {
        const id = Date.now().toString();
        setToasts((prev) => [...prev, { id, type, message }]);
    };

    const closeToast = (id: string) => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
    };

    return { toasts, showToast, closeToast };
};

export default Toast;

