interface UserAvatarProps {
  profileImageUrl?: string | null;
  nickname?: string | null;
  size?: number;
  className?: string;
}

export const UserAvatar = ({
  profileImageUrl,
  nickname,
  size = 36,
  className = '',
}: UserAvatarProps) => {
  const fallback = (nickname?.trim()?.[0] ?? '?').toUpperCase();

  if (profileImageUrl) {
    return (
      <img
        src={profileImageUrl}
        alt={nickname ?? '사용자 프로필'}
        className={`rounded-full object-cover bg-gray-100 ${className}`}
        style={{ width: size, height: size }}
      />
    );
  }

  return (
    <div
      className={`rounded-full bg-gray-100 text-gray-500 flex items-center justify-center font-bold ${className}`}
      style={{ width: size, height: size }}
    >
      {fallback}
    </div>
  );
};
