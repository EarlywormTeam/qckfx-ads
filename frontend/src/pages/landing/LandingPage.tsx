import React, { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import FeatureList from './FeatureList';
import VideoPlaceholder from './VideoPlaceholder';
import { useAPI } from '@/api';

const LandingPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const api = useAPI();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const waitlistAPI = api.createWaitlistAPI();
      const response = await waitlistAPI.joinWaitlist(email);
      setMessage(response);
      setEmail('');
    } catch {
      setMessage('An error occurred. Please try again.');
    }
  };

  return (
    <div className="h-full w-full bg-background-accent">
      <div className="w-full bg-gradient-to-b from-background-white to-background-accent pb-12 p-6">
        <main className="max-w-6xl mx-auto">
          <h1 className="text-4xl md:text-5xl font-sans font-black text-center text-text-darkPrimary mb-2">
            Pixel-Perfect Photos & Videos for Your Store
          </h1>
          <p className="text-4xl md:text-5xl text-center font-script text-text-darkPrimary font-bold italic mb-8">In Seconds</p>
        </main>
      </div>
      
      <main className="max-w-6xl mx-auto">
        <div className="flex flex-col md:flex-row gap-8">
          <div className="md:w-1/2">
            <FeatureList />
          </div>
          <div className="md:w-1/2">
            <VideoPlaceholder />
          </div>
        </div>
        
        <div className="mt-12">
          <h2 className="text-xl font-semibold text-center mb-2">Exclusive Invite-Only Access</h2>
          <p className="text-center mb-4">Our service is currently available by invitation only. Join the waitlist to receive an invite as soon as possible!</p>
          <form onSubmit={handleSubmit} className="flex gap-4">
            <Input
              placeholder="Enter your email address"
              className="flex-grow bg-background-white text-text-black"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              type="email"
              required
            />
            <Button type="submit" className="bg-background-action text-text-white">Join Waitlist</Button>
          </form>
          {message && <p className="text-center mt-2">{message}</p>}
        </div>
      </main>
    </div>
  );
};

export default LandingPage;