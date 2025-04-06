import React, { useState, useContext } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { toast } from 'react-toastify';
import { AuthContext } from '../context/AuthContext';
import { 
  Container, 
  Typography, 
  TextField, 
  Button, 
  Box, 
  Paper, 
  Grid, 
  CircularProgress
} from '@mui/material';

const Register = () => {
  const [userData, setUserData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    full_name: ''
  });
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const { register, login } = useContext(AuthContext);
  const navigate = useNavigate();
  
  const validateForm = () => {
    let tempErrors = {};
    
    if (!userData.username) {
      tempErrors.username = '请输入用户名';
    } else if (!/^[a-zA-Z0-9]+$/.test(userData.username)) {
      tempErrors.username = '用户名只能包含字母和数字';
    }
    
    if (!userData.email) {
      tempErrors.email = '请输入邮箱';
    } else if (!/\S+@\S+\.\S+/.test(userData.email)) {
      tempErrors.email = '邮箱格式不正确';
    }
    
    if (!userData.password) {
      tempErrors.password = '请输入密码';
    } else if (userData.password.length < 8) {
      tempErrors.password = '密码长度至少为8个字符';
    }
    
    if (userData.password !== userData.confirmPassword) {
      tempErrors.confirmPassword = '两次输入的密码不一致';
    }
    
    setErrors(tempErrors);
    return Object.keys(tempErrors).length === 0;
  };
  
  const handleChange = (e) => {
    const { name, value } = e.target;
    setUserData({
      ...userData,
      [name]: value
    });
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (validateForm()) {
      setIsSubmitting(true);
      
      try {
        // 移除确认密码字段，因为API不需要
        const { confirmPassword, ...registerData } = userData;
        
        // 注册用户
        await register(registerData);
        
        // 注册成功后自动登录
        await login({
          username: userData.username,
          password: userData.password
        });
        
        toast.success('注册成功！');
        navigate('/');
      } catch (err) {
        toast.error(err.message || '注册失败，请稍后再试');
      } finally {
        setIsSubmitting(false);
      }
    }
  };
  
  return (
    <Container component="main" maxWidth="xs">
      <Paper elevation={3} sx={{ p: 4, mt: 8 }}>
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <Typography component="h1" variant="h5">
            注册
          </Typography>
          
          <Box component="form" onSubmit={handleSubmit} sx={{ mt: 3 }}>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <TextField
                  autoComplete="username"
                  name="username"
                  required
                  fullWidth
                  id="username"
                  label="用户名"
                  autoFocus
                  value={userData.username}
                  onChange={handleChange}
                  error={!!errors.username}
                  helperText={errors.username}
                />
              </Grid>
              
              <Grid item xs={12}>
                <TextField
                  required
                  fullWidth
                  id="email"
                  label="邮箱"
                  name="email"
                  autoComplete="email"
                  value={userData.email}
                  onChange={handleChange}
                  error={!!errors.email}
                  helperText={errors.email}
                />
              </Grid>
              
              <Grid item xs={12}>
                <TextField
                  required
                  fullWidth
                  id="full_name"
                  label="全名"
                  name="full_name"
                  autoComplete="name"
                  value={userData.full_name}
                  onChange={handleChange}
                  error={!!errors.full_name}
                  helperText={errors.full_name}
                />
              </Grid>
              
              <Grid item xs={12}>
                <TextField
                  required
                  fullWidth
                  name="password"
                  label="密码"
                  type="password"
                  id="password"
                  autoComplete="new-password"
                  value={userData.password}
                  onChange={handleChange}
                  error={!!errors.password}
                  helperText={errors.password}
                />
              </Grid>
              
              <Grid item xs={12}>
                <TextField
                  required
                  fullWidth
                  name="confirmPassword"
                  label="确认密码"
                  type="password"
                  id="confirmPassword"
                  value={userData.confirmPassword}
                  onChange={handleChange}
                  error={!!errors.confirmPassword}
                  helperText={errors.confirmPassword}
                />
              </Grid>
            </Grid>
            
            <Button
              type="submit"
              fullWidth
              variant="contained"
              color="primary"
              sx={{ mt: 3, mb: 2 }}
              disabled={isSubmitting}
            >
              {isSubmitting ? <CircularProgress size={24} /> : '注册'}
            </Button>
            
            <Grid container justifyContent="flex-end">
              <Grid item>
                <Link to="/login" style={{ textDecoration: 'none' }}>
                  <Typography variant="body2" color="primary">
                    已有账号？登录
                  </Typography>
                </Link>
              </Grid>
            </Grid>
          </Box>
        </Box>
      </Paper>
    </Container>
  );
};

export default Register;