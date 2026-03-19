import type { User } from './types';

interface Props {
  users: User[];
  selectedUser: string;
  setSelectedUser: (v: string) => void;
  selectedMonth: string;
  setSelectedMonth: (v: string) => void;
  onLoad: () => void;
  statusMsg: string;
}

export function TopBar({ users, selectedUser, setSelectedUser, selectedMonth, setSelectedMonth, onLoad, statusMsg }: Props) {
  return (
    <section className="topbar">
      <div className="controls">
        <div>
          <label htmlFor="user-select">회원</label>
          <select 
            id="user-select" 
            value={selectedUser} 
            onChange={e => setSelectedUser(e.target.value)}
          >
            {users.map(u => (
              <option key={u.user_id} value={u.name}>{u.name} ({u.user_id})</option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="month-select">대상 월</label>
          <input 
            id="month-select" 
            type="month" 
            value={selectedMonth} 
            onChange={e => setSelectedMonth(e.target.value)}
          />
        </div>
      </div>
      <button id="load-button" type="button" onClick={onLoad}>통계 불러오기</button>
      <div id="status" className="status">{statusMsg}</div>
    </section>
  );
}
