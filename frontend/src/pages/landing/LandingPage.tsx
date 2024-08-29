import React from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import FeatureList from './FeatureList';
import VideoPlaceholder from './VideoPlaceholder';

const LandingPage: React.FC = () => {

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
          <h2 className="text-xl font-semibold text-center mb-4">Join the Waitlist:</h2>
          <div className="flex gap-4">
            <Input placeholder="Enter your email address" className="flex-grow bg-background-white text-text-black" />
            <Button className="bg-background-action text-text-white">Join Waitlist</Button>
          </div>
        </div>
      </main>
    </div>
  );
};

export default LandingPage;