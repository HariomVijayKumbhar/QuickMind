import { useEffect } from 'react';

export default function GoogleLoginButton({ onSuccess }) {
  useEffect(() => {
    if (!window.google) return;
    window.google.accounts.id.initialize({
      client_id: import.meta.env.VITE_GOOGLE_CLIENT_ID,
      callback: (response) => {
        if (response.credential) {
          onSuccess(response.credential);
        }
      },
    });
    window.google.accounts.id.renderButton(
      document.getElementById('google-button'),
      { theme: 'outline', size: 'large', width: '100%' }
    );
  }, [onSuccess]);

  return <div id="google-button" className="google-button" />;
}
