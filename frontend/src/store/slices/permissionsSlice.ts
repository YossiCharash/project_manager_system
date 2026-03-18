import { createAsyncThunk, createSelector, createSlice } from '@reduxjs/toolkit'
import api from '../../lib/api'
import type { RootState } from '../index'

interface Permission {
  resource_type: string
  action: string
  project_id?: number | null
}

interface PermissionsState {
  permissions: Permission[]
  loaded: boolean
  loading: boolean
  error: string | null
}

const initialState: PermissionsState = {
  permissions: [],
  loaded: false,
  loading: false,
  error: null,
}

export const fetchUserPermissions = createAsyncThunk(
  'permissions/fetchUserPermissions',
  async (userId: number, { rejectWithValue }) => {
    try {
      const { data } = await api.get<Permission[]>(`/iam/users/${userId}/permissions`)
      return data
    } catch {
      // Non-fatal: Admins bypass permission checks server-side.
      return rejectWithValue([])
    }
  }
)

const permissionsSlice = createSlice({
  name: 'permissions',
  initialState,
  reducers: {
    clearPermissions(state) {
      state.permissions = []
      state.loaded = false
      state.loading = false
      state.error = null
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchUserPermissions.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(fetchUserPermissions.fulfilled, (state, action) => {
        state.permissions = action.payload as Permission[]
        state.loaded = true
        state.loading = false
      })
      .addCase(fetchUserPermissions.rejected, (state) => {
        // Mark as loaded even on error so the UI doesn't hang on the loading
        // gate.  Admin users won't have explicit permissions but can still
        // access everything via server-side role checks.
        state.permissions = []
        state.loaded = true
        state.loading = false
      })
  },
})

export const { clearPermissions } = permissionsSlice.actions

/**
 * Returns true when the current user has *any* permission on the given
 * resource type (read, write, delete …).
 *
 * Admins always get `true` because the server grants them full access
 * regardless of stored permissions.
 */
export const selectHasAnyAccess = (resourceType: string) =>
  createSelector(
    (state: RootState) => state.permissions.permissions,
    (state: RootState) => state.auth.me,
    (permissions, me) => {
      if (me?.role === 'Admin') return true
      return permissions.some((p) => p.resource_type === resourceType)
    }
  )

export default permissionsSlice.reducer
