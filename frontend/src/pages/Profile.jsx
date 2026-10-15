import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { api } from '../services/api'
import toast from 'react-hot-toast'
import { HiUser, HiMail, HiPhone, HiSave, HiLockClosed } from 'react-icons/hi'

export default function Profile() {
  const { user, updateProfile } = useAuth()
  const [form, setForm] = useState({
    username: user?.username || '',
    phone: user?.phone || '',
  })
  const [pwForm, setPwForm] = useState({ current: '', new: '', confirm: '' })
  const [loading, setLoading] = useState(false)
  const [pwLoading, setPwLoading] = useState(false)

  const handleProfileSave = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      await updateProfile(form)
      toast.success('Profile updated!')
    } catch {} finally { setLoading(false) }
  }

  const handlePasswordChange = async (e) => {
    e.preventDefault()
    if (pwForm.new !== pwForm.confirm) { toast.error('Passwords do not match'); return }
    if (pwForm.new.length < 8) { toast.error('Password must be 8+ characters'); return }
    setPwLoading(true)
    try {
      await api.post('/auth/reset-password', {
        token: 'profile-change',
        new_password: pwForm.new,
      })
      toast.success('Password changed!')
      setPwForm({ current: '', new: '', confirm: '' })
    } catch {} finally { setPwLoading(false) }
  }

  return (
    <div className="space-y-6 max-w-2xl animate-fade-in">
      <div>
        <h1 className="page-title">Profile</h1>
        <p className="page-subtitle">Manage your account settings</p>
      </div>

      {/* Avatar Card */}
      <div className="glass-card p-6 flex items-center gap-5">
        <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-primary-500 to-purple-600 flex items-center justify-center text-3xl font-bold text-white shadow-xl shadow-primary-500/30">
          {user?.username?.[0]?.toUpperCase()}
        </div>
        <div>
          <p className="text-xl font-bold text-white">{user?.username}</p>
          <p className="text-slate-400">{user?.email}</p>
          <span className={`badge mt-2 ${user?.role === 'admin' ? 'badge-purple' : 'badge-blue'}`}>
            {user?.role}
          </span>
        </div>
      </div>

      {/* Profile Form */}
      <div className="glass-card p-6">
        <h2 className="text-base font-semibold text-white mb-5 flex items-center gap-2">
          <HiUser className="w-5 h-5 text-primary-400" />
          Personal Information
        </h2>
        <form onSubmit={handleProfileSave} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Username</label>
            <input
              type="text"
              value={form.username}
              onChange={(e) => setForm({ ...form, username: e.target.value })}
              className="input-field"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Email</label>
            <div className="relative">
              <HiMail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
              <input
                type="email"
                value={user?.email}
                disabled
                className="input-field pl-10 opacity-50 cursor-not-allowed"
              />
            </div>
            <p className="text-xs text-slate-500 mt-1">Email cannot be changed</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Phone</label>
            <div className="relative">
              <HiPhone className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
              <input
                type="tel"
                value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
                placeholder="+91 98765 43210"
                className="input-field pl-10"
              />
            </div>
          </div>
          <button type="submit" disabled={loading} className="btn-primary">
            <HiSave className="w-4 h-4" />
            {loading ? 'Saving...' : 'Save Changes'}
          </button>
        </form>
      </div>

      {/* Change Password */}
      <div className="glass-card p-6">
        <h2 className="text-base font-semibold text-white mb-5 flex items-center gap-2">
          <HiLockClosed className="w-5 h-5 text-primary-400" />
          Change Password
        </h2>
        <form onSubmit={handlePasswordChange} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">New Password</label>
            <input
              type="password"
              value={pwForm.new}
              onChange={(e) => setPwForm({ ...pwForm, new: e.target.value })}
              placeholder="Min 8 characters"
              className="input-field"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Confirm New Password</label>
            <input
              type="password"
              value={pwForm.confirm}
              onChange={(e) => setPwForm({ ...pwForm, confirm: e.target.value })}
              placeholder="Repeat new password"
              className="input-field"
            />
          </div>
          <button type="submit" disabled={pwLoading} className="btn-primary">
            <HiLockClosed className="w-4 h-4" />
            {pwLoading ? 'Updating...' : 'Change Password'}
          </button>
        </form>
      </div>

      {/* Account Info */}
      <div className="glass-card p-6">
        <h2 className="text-base font-semibold text-white mb-3">Account Info</h2>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-slate-400">Member since</span>
            <span className="text-slate-200">{new Date(user?.created_at).toLocaleDateString()}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Account status</span>
            <span className="badge badge-green">Active</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Role</span>
            <span className={`badge ${user?.role === 'admin' ? 'badge-purple' : 'badge-blue'}`}>{user?.role}</span>
          </div>
        </div>
      </div>
    </div>
  )
}
