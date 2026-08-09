import React, {useCallback, useState} from 'react';
import {Alert, SafeAreaView, StyleSheet, Text, TouchableOpacity, View} from 'react-native';
import type {CompositeScreenProps} from '@react-navigation/native';
import type {NativeStackScreenProps} from '@react-navigation/native-stack';
import type {BottomTabScreenProps} from '@react-navigation/bottom-tabs';
import WaveformIndicator from '@/components/WaveformIndicator';
import {processVoiceClip} from '@/api/voice';
import type {RootStackParamList, TabParamList} from '@/navigation/AppNavigator';

type Props = CompositeScreenProps<
  BottomTabScreenProps<TabParamList, 'Home'>,
  NativeStackScreenProps<RootStackParamList>
>;

type ListeningState = 'idle' | 'listening' | 'processing';

/**
 * Home/Listening screen (section 4.2 #1). Shows a passive listening
 * indicator and a waveform when active. Real always-on wake-word capture is
 * wired through services/wakeword.ts + services/backgroundService.ts, which
 * need a native build + Picovoice key to actually run (see mobile/README.md
 * and services/wakeword.ts for exactly what's missing). The manual
 * "Hold to talk" button below exercises the same POST /voice/process path
 * without depending on any of that, so the screen is testable in Expo Go /
 * simulator too.
 */
export default function HomeScreen({navigation}: Props) {
  const [state, setState] = useState<ListeningState>('idle');
  const [lastResponse, setLastResponse] = useState<string | null>(null);

  const handleManualCapture = useCallback(async () => {
    // NOTE: actual mic capture (react-native-audio-recorder-player or
    // similar) is not wired up here — this simulates the round trip using
    // a placeholder file URI so the screen and API layer can be exercised
    // end to end. Swap `mockAudioUri` for a real recorded clip's URI once
    // mic capture is integrated.
    setState('listening');
    const mockAudioUri = 'file:///dev/null';
    try {
      setState('processing');
      const result = await processVoiceClip(mockAudioUri);
      setLastResponse(result.response_text);
      if (result.proposed_action_id) {
        navigation.navigate('Confirmation', {actionId: result.proposed_action_id, summary: result.response_text});
      }
    } catch (err) {
      Alert.alert('Oreo', 'Could not reach the backend. Check Settings for the backend URL.');
    } finally {
      setState('idle');
    }
  }, [navigation]);

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.center}>
        <Text style={styles.title}>Oreo</Text>
        <Text style={styles.subtitle}>
          {state === 'idle' && 'Say "Oreo" or tap below'}
          {state === 'listening' && 'Listening…'}
          {state === 'processing' && 'Thinking…'}
        </Text>
        <WaveformIndicator active={state !== 'idle'} />
        {lastResponse ? <Text style={styles.response}>{lastResponse}</Text> : null}
      </View>

      <TouchableOpacity style={styles.captureButton} onPress={handleManualCapture} disabled={state !== 'idle'}>
        <Text style={styles.captureButtonText}>{state === 'idle' ? 'Hold to talk' : '…'}</Text>
      </TouchableOpacity>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {flex: 1, backgroundColor: '#0F0E17', justifyContent: 'space-between', padding: 24},
  center: {flex: 1, alignItems: 'center', justifyContent: 'center', gap: 12},
  title: {fontSize: 40, fontWeight: '700', color: '#FFFFFE'},
  subtitle: {fontSize: 16, color: '#A7A9BE'},
  response: {marginTop: 24, fontSize: 16, color: '#FFFFFE', textAlign: 'center', paddingHorizontal: 16},
  captureButton: {
    backgroundColor: '#6C5CE7',
    borderRadius: 32,
    paddingVertical: 18,
    alignItems: 'center',
    marginBottom: 24,
  },
  captureButtonText: {color: '#FFFFFE', fontSize: 18, fontWeight: '600'},
});
