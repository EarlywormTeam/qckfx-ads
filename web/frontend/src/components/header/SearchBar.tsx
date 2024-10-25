import { useState, useEffect, KeyboardEvent } from "react"
import { Search, X, User } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { Separator } from "@/components/ui/separator"
import { ScrollArea } from "@/components/ui/scroll-area"
import { ImageSearchRequest } from "@/types/search"
import { useNavigate, useLocation } from "react-router-dom"
import { useProducts } from "@/hooks/product/useProducts";
import { Product } from "@/types/product"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"

const PRESET_COLORS = [
  "#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF", "#00FFFF",
  "#FFA500", "#800080", "#008000", "#FFC0CB", "#A52A2A", "#808080"
]

const FACES = [1, 2, 3, 4, 5, 6]

function ColorCircles({ colors }: { colors: string[] }) {
  return (
    <div className="flex -space-x-2 overflow-hidden">
      {colors.map((color, index) => (
        <div
          key={color}
          className="w-6 h-6 rounded-full border-2 border-background"
          style={{ backgroundColor: color, zIndex: colors.length - index }}
        />
      ))}
    </div>
  )
}

function Facepile({ faces }: { faces: number[] }) {
  return (
    <div className="flex -space-x-2 overflow-hidden">
      {faces.map((face, index) => (
        <div
          key={face}
          className="w-6 h-6 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-xs font-bold border-2 border-background"
          style={{ zIndex: faces.length - index }}
        >
          {face}
        </div>
      ))}
    </div>
  )
}

function ProductPile({ products }: { products: Product[] }) {
  return (
    <div className="flex -space-x-2 overflow-hidden">
      {products.map((product, index) => (
        <TooltipProvider key={product.id}>
          <Tooltip>
            <TooltipTrigger asChild>
              <div
                className="w-6 h-6 rounded-full bg-secondary text-secondary-foreground flex items-center justify-center text-xs font-bold border-2 border-background overflow-hidden"
                style={{ zIndex: products.length - index }}
              >
                <img 
                  src={product.primaryImageUrl} 
                  alt={product.name} 
                  className="w-full h-full object-contain object-center"
                />
              </div>
            </TooltipTrigger>
            <TooltipContent>
              <p>{product.name}</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      ))}
    </div>
  )
}

export default function HeaderAdvancedSearch() {
  const [searchText, setSearchText] = useState("")
  const [selectedColors, setSelectedColors] = useState<string[]>([])
  const [selectedFaces, setSelectedFaces] = useState<number[]>([])
  const [selectedProducts, setSelectedProducts] = useState<Product[]>([])
  const [customColor, setCustomColor] = useState("#000000")
  const { products } = useProducts();

  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const searchParams = new URLSearchParams(location.search);
    setSearchText(searchParams.get("text") || "");
    
    const colorsParam = searchParams.get("colors");
    setSelectedColors(colorsParam && colorsParam !== "" ? colorsParam.split(",") : []);
    
    const facesParam = searchParams.get("faces");
    setSelectedFaces(facesParam && facesParam !== "" ? facesParam.split(",").map(Number).filter(Boolean) : []);
    
    const productsParam = searchParams.get("products");
    setSelectedProducts(
      productsParam && productsParam !== ""
        ? productsParam.split(",")
            .map(id => products?.find(p => p.id === id))
            .filter(Boolean) as Product[]
        : []
    );  
  }, [location, products]);

  const handleColorToggle = (color: string) => {
    setSelectedColors(prev => {
      const newColors = prev.includes(color) ? prev.filter(c => c !== color) : [...prev, color];
      handleSearch(searchText, newColors, selectedFaces, selectedProducts);
      return newColors;
    });
  }

  const handleFaceToggle = (faceId: number) => {
    setSelectedFaces(prev => {
      const newFaces = prev.includes(faceId) ? prev.filter(id => id !== faceId) : [...prev, faceId];
      handleSearch(searchText, selectedColors, newFaces, selectedProducts);
      return newFaces;
    });
  }

  const handleProductToggle = (product: Product) => {
    setSelectedProducts(prev => {
      const newProducts = prev.some(p => p.id === product.id) ? prev.filter(p => p.id !== product.id) : [...prev, product];
      handleSearch(searchText, selectedColors, selectedFaces, newProducts);
      return newProducts;
    });
  }

  const handleAddCustomColor = () => {
    if (!selectedColors.includes(customColor)) {
      const newColors = [...selectedColors, customColor];
      setSelectedColors(newColors);
      handleSearch(searchText, newColors, selectedFaces, selectedProducts);
    }
  }

  const handleSearch = (
    text: string = searchText,
    colors: string[] = selectedColors,
    faces: number[] = selectedFaces,
    products: Product[] = selectedProducts
  ) => {
    const searchParams: ImageSearchRequest = {
      text: text,
      dominant_colors: colors,
      faces: faces.map(face => face.toString()),
      products: products.map(product => product.id.toString()),
      page: 1,
      page_size: 20,
    };

    navigate({
      pathname: '/app/search',
      search: `?text=${encodeURIComponent(searchParams.text || "")}&colors=${encodeURIComponent(colors.join(","))}&faces=${encodeURIComponent(faces.join(","))}&products=${encodeURIComponent(products.map(p => p.id).join(","))}&page=1`,
    });
    
    console.log("Searching with:", {
      text: text,
      colors: colors,
      faces: faces,
      products: products,
    });
  }

  const handleKeyPress = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  }

  return (
    <div className="bg-background rounded-md shadow-sm">
      <div className="flex items-start space-x-2 mb-2">
        <Input
          type="text"
          placeholder="Enter search terms..."
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          onKeyDown={handleKeyPress}
          className="flex-grow"
        />
        <Button onClick={() => handleSearch()}>
          <Search className="w-4 h-4" />
          <span className="sr-only">Search</span>
        </Button>
      </div>
      <div className="flex flex-wrap items-start gap-2">
        <div className="flex items-center space-x-2">
          <Popover>
            <PopoverTrigger asChild>
              <Button variant="outline" className="w-[100px] relative">
                Colors
                {selectedColors.length > 0 && (
                  <span className="absolute top-0 right-0 -mt-1 -mr-1 bg-primary text-primary-foreground text-xs rounded-full w-5 h-5 flex items-center justify-center">
                    {selectedColors.length}
                  </span>
                )}
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-[200px]">
              <ScrollArea className="h-[300px] pr-4">
                <div className="space-y-2">
                  <div className="font-semibold mb-2">Preset Colors</div>
                  <div className="grid grid-cols-4 gap-2">
                    {PRESET_COLORS.map((color) => (
                      <button
                        key={color}
                        className={`w-8 h-8 rounded-md border-2 ${
                          selectedColors.includes(color) ? 'border-primary' : 'border-transparent'
                        }`}
                        style={{ backgroundColor: color }}
                        onClick={() => handleColorToggle(color)}
                      />
                    ))}
                  </div>
                  <Separator className="my-2" />
                  <div className="font-semibold mb-2">Custom Color</div>
                  <div className="flex items-center space-x-2">
                    <Input
                      type="color"
                      value={customColor}
                      onChange={(e) => setCustomColor(e.target.value)}
                      className="w-8 h-8 p-1 rounded-md"
                    />
                    <Button size="sm" onClick={handleAddCustomColor}>Add</Button>
                  </div>
                  {selectedColors.length > 0 && (
                    <>
                      <Separator className="my-2" />
                      <div className="font-semibold mb-2">Selected Colors</div>
                      <div className="flex flex-wrap gap-2">
                        {selectedColors.map((color) => (
                          <div key={color} className="relative">
                            <div
                              className="w-6 h-6 rounded-md"
                              style={{ backgroundColor: color }}
                            />
                            <button
                              className="absolute -top-1 -right-1 bg-destructive text-destructive-foreground rounded-full w-4 h-4 flex items-center justify-center"
                              onClick={() => handleColorToggle(color)}
                            >
                              <X className="w-3 h-3" />
                            </button>
                          </div>
                        ))}
                      </div>
                    </>
                  )}
                </div>
              </ScrollArea>
            </PopoverContent>
          </Popover>
          {selectedColors.length > 0 && <ColorCircles colors={selectedColors} />}
        </div>

        <div className="flex items-center space-x-2">
          <Popover>
            <PopoverTrigger asChild>
              <Button variant="outline" className="w-[100px] relative">
                Faces
                {selectedFaces.length > 0 && (
                  <span className="absolute top-0 right-0 -mt-1 -mr-1 bg-primary text-primary-foreground text-xs rounded-full w-5 h-5 flex items-center justify-center">
                    {selectedFaces.length}
                  </span>
                )}
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-[200px]">
              <ScrollArea className="h-[200px] pr-4">
                <div className="space-y-2">
                  <div className="font-semibold mb-2">Select Faces</div>
                  <div className="grid grid-cols-3 gap-2">
                    {FACES.map((faceId) => (
                      <Button
                        key={faceId}
                        variant={selectedFaces.includes(faceId) ? "default" : "outline"}
                        className="w-12 h-12"
                        onClick={() => handleFaceToggle(faceId)}
                      >
                        <User className="w-6 h-6" />
                      </Button>
                    ))}
                  </div>
                </div>
              </ScrollArea>
            </PopoverContent>
          </Popover>
          {selectedFaces.length > 0 && <Facepile faces={selectedFaces} />}
        </div>

        <div className="flex items-center space-x-2">
          <Popover>
            <PopoverTrigger asChild>
              <Button variant="outline" className="w-[100px] relative">
                Products
                {selectedProducts.length > 0 && (
                  <span className="absolute top-0 right-0 -mt-1 -mr-1 bg-primary text-primary-foreground text-xs rounded-full w-5 h-5 flex items-center justify-center">
                    {selectedProducts.length}
                  </span>
                )}
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-[250px]">
              <ScrollArea className="h-[200px] pr-4">
                <div className="space-y-2">
                  <div className="font-semibold mb-2">Select Products</div>
                  <div className="grid gap-2">
                    {products?.map((product) => (
                      <Button
                        key={product.id}
                        variant={selectedProducts.some(p => p.id === product.id) ? "default" : "outline"}
                        className="h-10 justify-start px-2 w-full"
                        onClick={() => handleProductToggle(product)}
                      >
                        <div className="w-6 h-6 rounded-full flex items-center justify-center overflow-hidden mr-2 flex-shrink-0">
                          <img 
                            src={product.primaryImageUrl} 
                            alt={product.name} 
                            className="max-w-full max-h-full object-contain"
                          />
                        </div>
                        <span className="truncate">{product.name}</span>
                      </Button>
                    ))}
                  </div>
                </div>
              </ScrollArea>
            </PopoverContent>
          </Popover>
          {selectedProducts.length > 0 && <ProductPile products={selectedProducts} />}
        </div>
      </div>
    </div>
  )
}
