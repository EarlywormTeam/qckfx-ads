import React from 'react';

const features = [
  { icon: '/icons/megaphone.svg', text: "Create the perfect marketing content" },
  { icon: '/icons/money.svg', text: "No expensive or complicated editing tools" },
  { icon: '/icons/gear.svg', text: "Specialized for your products" },
  { icon: '/icons/images.svg', text: "Unlimited image generations" },
  { icon: '/icons/video.svg', text: "Make images and video (Beta)" },
];

const FeatureList: React.FC = () => {
  return (
    <ul className="pt-6 space-y-8">
      {features.map((feature, index) => (
        <li key={index} className="flex items-center gap-3">
          <img src={feature.icon} alt="" className="w-6 h-6 text-text-black" />
          <span className="text-text-black font-medium">
            {feature.text.split('your').map((part, i) => 
              i > 0 ? [<span key={i} className="text-text-darkAccent font-extrabold italic">your</span>, part] : part
            )}
          </span>
        </li>
      ))}
    </ul>
  );
};

export default FeatureList;