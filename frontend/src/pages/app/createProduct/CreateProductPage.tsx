import React, { useState, useEffect } from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Upload } from 'lucide-react';
import { useToast } from "@/components/ui/use-toast";

const CreateProductPage: React.FC = () => {
  const [productName, setProductName] = useState('');
  const [primaryImage, setPrimaryImage] = useState<File | null>(null);
  const [additionalImages, setAdditionalImages] = useState<File[]>([]);
  const [isFormValid, setIsFormValid] = useState(false);

  const { toast } = useToast();

  useEffect(() => {
    setIsFormValid(productName.trim() !== '' && primaryImage !== null);
  }, [productName, primaryImage]);

  const handlePrimaryImageUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      setPrimaryImage(event.target.files[0]);
    }
  };

  const handleAdditionalImagesUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files) {
      setAdditionalImages(prevImages => [...prevImages, ...Array.from(event.target.files || [])].slice(0, 20));
    }
  };

  const handleSubmit = () => {
    if (!isFormValid) {
      toast({
        title: "Error",
        description: "Product name and primary image are required.",
        variant: "destructive",
      });
      return;
    }
    // Proceed with form submission
    // ... add your submission logic here ...
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold text-text-darkPrimary mb-8">Create New Product</h1>
      
      <div className="mb-6">
        <label htmlFor="productName" className="block text-sm font-medium text-text-darkPrimary mb-2">
          Product Name <span className="text-red-500">*</span>
        </label>
        <Input
          id="productName"
          type="text"
          value={productName}
          onChange={(e) => setProductName(e.target.value)}
          placeholder="Enter product name"
          className="w-full"
        />
      </div>

      <div className="mb-6">
        <label className="block text-sm font-medium text-text-darkPrimary mb-2">
          Primary Product Image <span className="text-red-500">*</span>
        </label>
        <div className="mt-2 flex justify-center px-6 pt-5 pb-6 border-2 border-dashed border-background-accent rounded-md">
          <div className="space-y-1 text-center">
            {primaryImage ? (
              <img src={URL.createObjectURL(primaryImage)} alt="Primary product" className="mx-auto h-64 w-64 object-cover" />
            ) : (
              <Upload className="mx-auto h-12 w-12 text-text-darkAccent" />
            )}
            <div className="flex text-sm text-text-darkPrimary">
              <label htmlFor="primary-image-upload" className="relative cursor-pointer bg-background-white rounded-md font-medium text-text-brand hover:text-text-darkAccent focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-text-brand">
                <span>{primaryImage ? 'Change image' : 'Upload image'}</span>
                <input id="primary-image-upload" name="primary-image-upload" type="file" className="sr-only" onChange={handlePrimaryImageUpload} accept="image/*" />
              </label>
            </div>
          </div>
        </div>
        <p className="mt-2 text-sm text-text-darkAccent">Upload a high-quality, close-up image of the product with all details clearly visible.</p>
      </div>

      <div className="mb-6">
        <label className="block text-sm font-medium text-text-darkPrimary mb-2">Additional Product Images (Optional, but Recommended)</label>
        <div className="mt-2 grid grid-cols-3 gap-4">
          {additionalImages.map((image, index) => (
            <img key={index} src={URL.createObjectURL(image)} alt={`Additional ${index + 1}`} className="h-32 w-full object-cover rounded-md" />
          ))}
          {additionalImages.length < 20 && (
            <div className="h-32 w-full flex items-center justify-center border-2 border-dashed border-background-accent rounded-md">
              <label htmlFor="additional-images-upload" className="cursor-pointer">
                <Upload className="mx-auto h-8 w-8 text-text-darkAccent" />
                <span className="mt-2 block text-sm font-medium text-text-darkPrimary">Add image</span>
                <input
                  id="additional-images-upload"
                  type="file"
                  multiple
                  className="sr-only"
                  onChange={handleAdditionalImagesUpload}
                  accept="image/*"
                />
              </label>
            </div>
          )}
        </div>
        <p className="mt-2 text-sm text-text-darkAccent">
          Add up to 20 images showing the product in various environments and angles. The more diverse images you provide, the better the AI-generated results will be.
        </p>
        <p className="mt-1 text-sm text-text-darkAccent">
          For optimal results, include images of the product in different lighting conditions, backgrounds, and use cases.
        </p>
      </div>

      <Button 
        className="w-full bg-background-action text-text-white hover:bg-background-dark disabled:opacity-50 disabled:cursor-not-allowed"
        onClick={handleSubmit}
      >
        Create Product
      </Button>
    </div>
  );
};

export default CreateProductPage;
