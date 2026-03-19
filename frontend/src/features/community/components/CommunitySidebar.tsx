import { NavLink, useLocation } from 'react-router-dom';

const CategoryIcon = ({ type }: { type: string | null }) => {
  const base = 'w-[18px] h-[18px] flex items-center justify-center flex-shrink-0';

  switch (type) {
    case null:
      return (
        <svg className={base} viewBox="0 0 18 18" fill="none" xmlns="http://www.w3.org/2000/svg">
          <rect x="2" y="2" width="5.5" height="5.5" rx="1.5" fill="currentColor" opacity="0.7" />
          <rect
            x="10.5"
            y="2"
            width="5.5"
            height="5.5"
            rx="1.5"
            fill="currentColor"
            opacity="0.4"
          />
          <rect
            x="2"
            y="10.5"
            width="5.5"
            height="5.5"
            rx="1.5"
            fill="currentColor"
            opacity="0.4"
          />
          <rect
            x="10.5"
            y="10.5"
            width="5.5"
            height="5.5"
            rx="1.5"
            fill="currentColor"
            opacity="0.7"
          />
        </svg>
      );
    case 'FREE':
      return (
        <svg className={base} viewBox="0 0 18 18" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path
            d="M3 4.5C3 3.67 3.67 3 4.5 3H13.5C14.33 3 15 3.67 15 4.5V11.5C15 12.33 14.33 13 13.5 13H6L3 15.5V4.5Z"
            fill="currentColor"
            opacity="0.6"
          />
        </svg>
      );
    case 'PR':
      return (
        <svg className={base} viewBox="0 0 18 18" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="9" cy="9" r="6.5" stroke="currentColor" strokeWidth="1.5" opacity="0.6" />
          <path
            d="M9 5.5V9.5L11.5 11"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            opacity="0.6"
          />
        </svg>
      );
    case 'COHORT':
      return (
        <svg className={base} viewBox="0 0 18 18" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="9" cy="6" r="3" fill="currentColor" opacity="0.6" />
          <path
            d="M3.5 15C3.5 12 6 10 9 10C12 10 14.5 12 14.5 15"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            opacity="0.5"
          />
        </svg>
      );
    case 'POLL':
      return (
        <svg className={base} viewBox="0 0 18 18" fill="none" xmlns="http://www.w3.org/2000/svg">
          <rect x="3" y="3" width="4" height="12" rx="1" fill="currentColor" opacity="0.5" />
          <rect x="10" y="7" width="4" height="8" rx="1" fill="currentColor" opacity="0.7" />
        </svg>
      );
    case 'HOTDEAL':
      return (
        <svg className={base} viewBox="0 0 18 18" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path
            d="M9 2L11 7H16L12 10.5L13.5 16L9 12.5L4.5 16L6 10.5L2 7H7L9 2Z"
            fill="currentColor"
            opacity="0.6"
          />
        </svg>
      );
    default:
      return (
        <div
          className={`${base} rounded-full bg-current opacity-40`}
          style={{ width: 6, height: 6 }}
        />
      );
  }
};

export const CommunitySidebar = () => {
  const location = useLocation();
  const searchParams = new URLSearchParams(location.search);
  const currentCategory = searchParams.get('category');

  const links = [
    { label: '전체 게시판', category: null },
    { label: '자유 게시판', category: 'FREE' },
    { label: 'PR 게시판', category: 'PR' },
    { label: '기수 게시판', category: 'COHORT' },
    { label: '토론 게시판', category: 'POLL' },
    { label: '핫딜 게시판', category: 'HOTDEAL' },
  ];

  return (
    <nav className="bg-white rounded-2xl p-4 shadow-[0_1px_3px_rgba(0,0,0,0.04)] border border-gray-100/80 flex flex-col gap-0.5">
      <div className="px-3 pt-2 pb-5 flex items-center gap-2.5">
        <div className="w-[3px] h-[18px] bg-primary-blue rounded-full" />
        <h3 className="text-[17px] font-bold text-gray-900 tracking-[-0.01em]">커뮤니티</h3>
      </div>

      {links.map((link) => {
        const isActive = currentCategory === link.category || (!currentCategory && !link.category);
        const to = link.category ? `/community?category=${link.category}` : '/community';

        return (
          <NavLink
            key={link.label}
            to={to}
            className={() =>
              `px-3 py-2.5 rounded-lg text-[13.5px] font-semibold transition-all duration-150 flex items-center gap-2.5 ${
                isActive
                  ? 'bg-blue-50 text-blue-600 font-bold'
                  : 'text-gray-500 hover:bg-gray-50 hover:text-gray-800'
              }`
            }
          >
            <CategoryIcon type={link.category} />
            {link.label}
          </NavLink>
        );
      })}
    </nav>
  );
};
