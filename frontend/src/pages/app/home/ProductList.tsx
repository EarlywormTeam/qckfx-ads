import { VariableSizeGrid as Grid } from 'react-window';
import { useEffect, useState, useRef } from 'react';
import { Plus } from 'lucide-react'; // Add this import for the plus icon
import { useNavigate } from 'react-router-dom'; // Add this import

const PRODUCTS = [
  {
    id: "1",
    name: "Bliss Can",
    imagePath: "/crunchy/products/1.jpeg",
    createdBy: "Megan Riggs",
    createdDate: "8/30/2024"
  },
  {
    id: "2",
    name: "Calm Can",
    imagePath: "/crunchy/products/2.jpeg",
    createdBy: "Chris Wood",
    createdDate: "8/29/2024",
  },
  {
    id: "3",
    name: "Elevate Can",
    imagePath: "/crunchy/products/3.jpeg",
    createdBy: "Chris Wood",
    createdDate: "8/29/2024",
  },
  {
    id: "4",
    name: "Energize Can",
    imagePath: "/crunchy/products/4.jpeg",
    createdBy: "Chris Wood",
    createdDate: "8/29/2024",
  },
];

const Cell: React.FC<{ columnIndex: number; rowIndex: number; style: React.CSSProperties }> = ({ columnIndex, rowIndex, style }) => {
  const navigate = useNavigate(); // Add this hook
  const index = rowIndex * 3 + columnIndex;
  const product = PRODUCTS[index];

  if (index === PRODUCTS.length) {
    // Render the "Add New Product" cell
    return (
      <div 
        style={{...style}}
        className="cursor-pointer bg-background-white transition-all duration-200 flex flex-col items-center justify-center group rounded-lg shadow-sm hover:shadow-md"
        onClick={() => navigate('/app/product/create')} // Add this onClick handler
      >
        <Plus size={48} className="text-text-darkPrimary transition-transform duration-200 group-hover:scale-110" />
        <span className="mt-2 text-sm font-medium text-text-darkPrimary">Add New Product</span>
      </div>
    );
  }

  if (!product) return null;

  return (
    <div 
      style={{...style}}
      className="cursor-pointer bg-background-white hover:bg-gray-50 transition-all duration-200 flex flex-col group rounded-b-lg shadow-sm hover:shadow-md"
      onClick={() => navigate(`/app/product/${encodeURIComponent(product.name)}`, { state: { product } })}
    >
      <div className="w-full h-32 mb-2 flex items-center justify-center overflow-hidden">
        <img 
          src={product.imagePath} 
          alt={product.name} 
          className="max-w-full max-h-full object-contain transition-transform duration-200 group-hover:scale-110" 
        />
      </div>
      <div className="bg-background-accent p-3 rounded-b-lg flex-grow">
        <h3 className="font-bold mb-2 text-text-darkPrimary group-hover:text-text-darkPrimary/90">{product.name}</h3>
        <div className="flex flex-col text-sm text-text-primary group-hover:text-text-primary/90">
          <span>Created By: {product.createdBy}</span>
          <span>{product.createdDate}</span>
        </div>
      </div>
    </div>
  );
};

const ProductList: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [containerWidth, setContainerWidth] = useState(0);

  useEffect(() => {
    const updateWidth = () => {
      if (containerRef.current) {
        setContainerWidth(containerRef.current.offsetWidth);
      }
    };

    updateWidth();
    window.addEventListener('resize', updateWidth);
    return () => window.removeEventListener('resize', updateWidth);
  }, []);

  const gap = 20;
  const minCellWidth = 280;
  const cellHeight = 340;

  const columnCount = Math.max(1, Math.floor((containerWidth + gap) / (minCellWidth + gap)));
  const cellWidth = (containerWidth - (columnCount - 1) * gap) / columnCount;
  const totalProducts = PRODUCTS.length + 1; // Add 1 for the "Add New Product" cell
  const rowCount = Math.ceil(totalProducts / columnCount);

  const getColumnWidth = () => cellWidth + gap;
  const getRowHeight = () => cellHeight + gap;

  const totalHeight = rowCount * (cellHeight + gap) - gap;

  return (
    <div ref={containerRef} style={{ width: '100%', height: '100%' }}>
      {containerWidth > 0 && (
        <Grid
          columnCount={columnCount}
          columnWidth={getColumnWidth}
          height={totalHeight}
          rowCount={rowCount}
          rowHeight={getRowHeight}
          width={containerWidth}
          style={{ overflow: 'visible' }}
        >
          {({ columnIndex, rowIndex, style }) => (
            <div style={{
              ...style,
              width: cellWidth,
              height: cellHeight,
              left: columnIndex * (cellWidth + gap),
              top: rowIndex * (cellHeight + gap),
              marginTop: rowIndex === 0 ? '2rem' : '0', // Add extra spacing for the first row
            }}>
              <Cell columnIndex={columnIndex} rowIndex={rowIndex} style={{}} />
            </div>
          )}
        </Grid>
      )}
    </div>
  );
};

export default ProductList;
