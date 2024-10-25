import { useEffect, useMemo, useState, useCallback, useRef } from "react"
import { useLocation, useNavigate } from "react-router-dom"
import ImageCard from "@/components/ImageCard"
import Pagination from "@/components/Pagination"
import { useAssetAPI } from "@/api/asset"
import { ImageSearchResponse } from "@/types/search"
import { Image } from "@/types/image"
import { useOrganization } from '@/hooks/organization/useOrganization';

export default function SearchResults() {
  const location = useLocation()
  const navigate = useNavigate()
  const api = useAssetAPI()
  const { organization } = useOrganization();
  const [images, setImages] = useState<Image[]>([])
  const [/*total*/, setTotal] = useState(0)
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [totalPages, setTotalPages] = useState(1)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  // Retry state to prevent infinite loops
  const [retryCount, setRetryCount] = useState(0)
  const maxRetries = 3

  // Add a ref for the AbortController
  const abortControllerRef = useRef<AbortController | null>(null);

  // Parse query parameters with proper memoization
  const { text, colors, faces, products, page } = useMemo(() => {
    const queryParams = new URLSearchParams(location.search)
    const text = queryParams.get("text") || ""
    const colors = queryParams.get("colors") ? queryParams.get("colors")!.split(",") : []
    const faces = queryParams.get("faces") ? queryParams.get("faces")!.split(",") : []
    const products = queryParams.get("products") ? queryParams.get("products")!.split(",") : []
    const page = queryParams.get("page") ? parseInt(queryParams.get("page")!) : 1

    return { text, colors, faces, products, page }
  }, [location.search])

  // Memoize the fetch function to prevent unnecessary re-creations
  const fetchSearchResults = useCallback(async () => {
    if (!organization) {
      setError("Organization not selected.");
      return;
    }

    // Abort any existing request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Create a new AbortController
    abortControllerRef.current = new AbortController();

    setLoading(true);
    setError(null);
    try {
      const searchRequest = {
        text: text,
        dominant_colors: colors,
        faces: faces,
        products: products,
        page: page,
        page_size: pageSize,
      };

      const response: ImageSearchResponse = await api.searchImages(organization.id, searchRequest, abortControllerRef.current.signal);
      setImages(response.images);
      setTotal(response.total);
      setCurrentPage(response.page);
      setPageSize(response.pageSize);
      setTotalPages(response.totalPages);
      setRetryCount(0); // Reset retry count on success
    } catch (err: unknown) {
      if (err instanceof Error && err.name === 'AbortError') {
        console.log('Request was aborted');
        return; // Skip setting error for aborted requests
      }
      console.error("Search failed:", err);
      setError("Failed to load search results.");
      setRetryCount(prev => prev + 1);
    } finally {
      setLoading(false);
    }
  }, [api, organization, text, colors, faces, products, page, pageSize]);

  useEffect(() => {
    if (retryCount >= maxRetries) {
      console.warn("Max retries reached.");
      return;
    }

    fetchSearchResults();

    return () => {
      // Cleanup: abort any ongoing request when the component unmounts or when the effect re-runs
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [fetchSearchResults, retryCount, maxRetries]);

  const handlePageChange = (newPage: number) => {
    navigate({
      pathname: "/search",
      search: `?text=${encodeURIComponent(text)}&colors=${encodeURIComponent(colors.join(","))}&faces=${encodeURIComponent(faces.join(","))}&products=${encodeURIComponent(products.join(","))}&page=${newPage}`,
    })
  }

  const handleImageClick = (image: Image) => {
    navigate(`/app/editor/${image.id}`)
  }

  return (
    <div className="search-results-container p-4">
      <h1 className="text-2xl mb-4">Search Results</h1>
      {loading && <div>Loading search results...</div>}
      {error && <div className="text-red-500">{error}</div>}
      {!loading && !error && images.length === 0 && <div>No images found.</div>}
      {!loading && !error && images.length > 0 && (
        <>
          {/* Pinterest-style Masonry Grid */}
          <div className="columns-1 sm:columns-2 md:columns-3 lg:columns-4 gap-4">
            {images.map(image => (
              <ImageCard key={image.id} image={image} onClick={handleImageClick} />
            ))}
          </div>
          <Pagination 
            currentPage={currentPage}
            totalPages={totalPages}
            onPageChange={handlePageChange}
          />
        </>
      )}
    </div>
  )
}
