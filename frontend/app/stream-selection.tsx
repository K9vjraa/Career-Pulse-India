import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  SafeAreaView,
  StatusBar,
  Dimensions,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';

const { width } = Dimensions.get('window');
const EXPO_PUBLIC_BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

interface Stream {
  id: string;
  title: string;
  description: string;
  icon: string;
  color: string;
  careers: string[];
}

const streams: Stream[] = [
  {
    id: 'Science',
    title: 'Science',
    description: 'Explore technology, research, and medical careers',
    icon: 'flask',
    color: '#4ECDC4',
    careers: ['Full Stack Developer', 'Data Scientist', 'Doctor', 'Engineer', 'Biotechnologist']
  },
  {
    id: 'Commerce',
    title: 'Commerce',
    description: 'Business, finance, and entrepreneurship paths',
    icon: 'trending-up',
    color: '#FFD93D',
    careers: ['Chartered Accountant', 'Investment Banker', 'Business Analyst', 'Marketing Manager', 'Entrepreneur']
  },
  {
    id: 'Arts',
    title: 'Arts',
    description: 'Creative, social, and humanities fields',
    icon: 'brush',
    color: '#FF6B6B',
    careers: ['Teacher', 'Designer', 'Journalist', 'Psychologist', 'Writer']
  }
];

export default function StreamSelectionScreen() {
  const router = useRouter();
  const [selectedStream, setSelectedStream] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleStreamSelect = (streamId: string) => {
    setSelectedStream(streamId);
  };

  const handleContinue = async () => {
    if (!selectedStream) {
      Alert.alert('Error', 'Please select a stream to continue');
      return;
    }

    setLoading(true);

    try {
      const token = await AsyncStorage.getItem('auth_token');
      if (!token) {
        Alert.alert('Error', 'Authentication required');
        router.replace('/auth/login');
        return;
      }

      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/user/stream`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          stream: selectedStream,
        }),
      });

      if (response.ok) {
        // Update local user data
        const userData = await AsyncStorage.getItem('user_data');
        if (userData) {
          const parsedUserData = JSON.parse(userData);
          parsedUserData.selected_stream = selectedStream;
          await AsyncStorage.setItem('user_data', JSON.stringify(parsedUserData));
        }

        router.replace('/dashboard');
      } else {
        Alert.alert('Error', 'Failed to update stream preference');
      }
    } catch (error) {
      console.error('Stream selection error:', error);
      Alert.alert('Error', 'Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#1a1a2e" />
      
      <LinearGradient
        colors={['#1a1a2e', '#16213e', '#0f3460']}
        style={styles.gradient}
      >
        <View style={styles.content}>
          
          {/* Header */}
          <View style={styles.header}>
            <Text style={styles.title}>Choose Your Stream</Text>
            <Text style={styles.subtitle}>
              Select your academic background to see relevant career roadmaps
            </Text>
          </View>

          {/* Stream Cards */}
          <View style={styles.streamsContainer}>
            {streams.map((stream) => (
              <TouchableOpacity
                key={stream.id}
                style={[
                  styles.streamCard,
                  selectedStream === stream.id && styles.selectedCard
                ]}
                onPress={() => handleStreamSelect(stream.id)}
                activeOpacity={0.8}
              >
                <LinearGradient
                  colors={
                    selectedStream === stream.id
                      ? [stream.color + '20', stream.color + '10']
                      : ['rgba(255, 255, 255, 0.1)', 'rgba(255, 255, 255, 0.05)']
                  }
                  style={styles.cardGradient}
                >
                  <View style={styles.cardContent}>
                    {/* Icon */}
                    <View style={[styles.iconContainer, { backgroundColor: stream.color + '20' }]}>
                      <Ionicons 
                        name={stream.icon as any} 
                        size={32} 
                        color={stream.color} 
                      />
                    </View>

                    {/* Content */}
                    <View style={styles.textContainer}>
                      <Text style={styles.streamTitle}>{stream.title}</Text>
                      <Text style={styles.streamDescription}>{stream.description}</Text>
                      
                      {/* Career examples */}
                      <View style={styles.careersContainer}>
                        <Text style={styles.careersLabel}>Career Paths:</Text>
                        <Text style={styles.careersText}>
                          {stream.careers.slice(0, 3).join(', ')}...
                        </Text>
                      </View>
                    </View>

                    {/* Selection Indicator */}
                    <View style={styles.selectionIndicator}>
                      {selectedStream === stream.id ? (
                        <View style={[styles.selectedIndicator, { backgroundColor: stream.color }]}>
                          <Ionicons name="checkmark" size={16} color="#FFFFFF" />
                        </View>
                      ) : (
                        <View style={styles.unselectedIndicator} />
                      )}
                    </View>
                  </View>
                </LinearGradient>
              </TouchableOpacity>
            ))}
          </View>

          {/* Continue Button */}
          <View style={styles.buttonContainer}>
            <TouchableOpacity 
              style={[styles.continueButton, (!selectedStream || loading) && styles.disabledButton]} 
              onPress={handleContinue}
              disabled={!selectedStream || loading}
            >
              <LinearGradient
                colors={
                  !selectedStream || loading 
                    ? ['#666', '#666'] 
                    : ['#4ECDC4', '#44A08D']
                }
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 0 }}
                style={styles.buttonGradient}
              >
                {loading ? (
                  <ActivityIndicator size="small" color="#FFFFFF" />
                ) : (
                  <>
                    <Text style={styles.buttonText}>Continue</Text>
                    <Ionicons name="arrow-forward" size={20} color="#FFFFFF" />
                  </>
                )}
              </LinearGradient>
            </TouchableOpacity>
          </View>
        </View>
      </LinearGradient>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  gradient: {
    flex: 1,
  },
  content: {
    flex: 1,
    paddingHorizontal: 24,
    paddingTop: 32,
  },
  header: {
    alignItems: 'center',
    marginBottom: 40,
  },
  title: {
    fontSize: 32,
    fontWeight: '700',
    color: '#FFFFFF',
    textAlign: 'center',
    marginBottom: 12,
  },
  subtitle: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.7)',
    textAlign: 'center',
    lineHeight: 24,
  },
  streamsContainer: {
    flex: 1,
    gap: 20,
  },
  streamCard: {
    borderRadius: 16,
    overflow: 'hidden',
    borderWidth: 2,
    borderColor: 'transparent',
  },
  selectedCard: {
    borderColor: '#4ECDC4',
    elevation: 8,
    shadowColor: '#4ECDC4',
    shadowOffset: {
      width: 0,
      height: 4,
    },
    shadowOpacity: 0.3,
    shadowRadius: 8,
  },
  cardGradient: {
    padding: 20,
  },
  cardContent: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  iconContainer: {
    width: 60,
    height: 60,
    borderRadius: 30,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 16,
  },
  textContainer: {
    flex: 1,
  },
  streamTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 4,
  },
  streamDescription: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.7)',
    lineHeight: 20,
    marginBottom: 12,
  },
  careersContainer: {
    marginTop: 4,
  },
  careersLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#4ECDC4',
    marginBottom: 2,
  },
  careersText: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.6)',
    lineHeight: 16,
  },
  selectionIndicator: {
    marginLeft: 12,
  },
  selectedIndicator: {
    width: 24,
    height: 24,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  unselectedIndicator: {
    width: 24,
    height: 24,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: 'rgba(255, 255, 255, 0.3)',
  },
  buttonContainer: {
    paddingVertical: 32,
  },
  continueButton: {
    borderRadius: 12,
    elevation: 4,
    shadowColor: '#4ECDC4',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.25,
    shadowRadius: 4,
  },
  disabledButton: {
    elevation: 0,
    shadowOpacity: 0,
  },
  buttonGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    gap: 8,
  },
  buttonText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#FFFFFF',
  },
});