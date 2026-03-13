import { useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import axios from 'axios';
import { useAuth, API } from '@/App';

/**
 * Hook to check if user has a pending payment and redirect to checkout
 * Call this on protected pages to ensure payment is completed
 */
export function usePendingPaymentCheck() {
  const { user, subscription } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    // Skip check on certain pages
    const allowedPaths = ['/checkout/success', '/pricing', '/login', '/', '/terms', '/privacy', '/legal', '/contact', '/faq', '/about', '/gdpr'];
    if (allowedPaths.some(path => location.pathname.startsWith(path))) {
      return;
    }

    // Check if user has a pending plan in localStorage
    const pendingPlan = localStorage.getItem('pending_plan');
    
    if (user && pendingPlan && pendingPlan !== 'free') {
      // User is logged in and has a pending paid plan
      // Check if subscription matches the pending plan
      const currentPlan = subscription?.plan || 'free';
      const isSubscriptionActive = subscription?.status === 'active';
      
      if (currentPlan !== pendingPlan || !isSubscriptionActive) {
        // Subscription doesn't match pending plan - redirect to pricing for checkout
        console.log('Pending payment detected, redirecting to checkout...');
        navigate(`/pricing?complete_checkout=${pendingPlan}`);
      } else {
        // Payment completed - clear pending plan
        localStorage.removeItem('pending_plan');
      }
    }
  }, [user, subscription, location.pathname, navigate]);
}

/**
 * Component wrapper that enforces payment completion
 */
export function PaymentGuard({ children }) {
  usePendingPaymentCheck();
  return children;
}

/**
 * Redirect to checkout for a specific plan
 */
export async function redirectToCheckout(plan) {
  try {
    const response = await axios.post(
      `${API}/checkout/session`,
      {
        plan,
        success_url: `${window.location.origin}/checkout/success?session_id={CHECKOUT_SESSION_ID}`,
        cancel_url: `${window.location.origin}/pricing?payment=cancelled`
      },
      { withCredentials: true }
    );
    
    window.location.href = response.data.url;
    return true;
  } catch (error) {
    console.error('Checkout redirect error:', error);
    return false;
  }
}

export default PaymentGuard;
