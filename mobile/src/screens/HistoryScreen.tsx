import React, {useCallback, useEffect, useState} from 'react';
import {FlatList, RefreshControl, SafeAreaView, StyleSheet, Text, View} from 'react-native';
import {getUserContext} from '@/api/context';
import {useAuth} from '@/context/AuthContext';
import type {ConversationTurn} from '@/api/types';

/** Conversation history (section 4.2 #3): scrollable transcript of recent
 * exchanges, pulled from GET /context/user/{id}. */
export default function HistoryScreen() {
  const {userId} = useAuth();
  const [turns, setTurns] = useState<ConversationTurn[]>([]);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    if (!userId) {
      return;
    }
    setRefreshing(true);
    try {
      const ctx = await getUserContext(userId);
      setTurns(ctx.recent_interactions);
    } finally {
      setRefreshing(false);
    }
  }, [userId]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <SafeAreaView style={styles.container}>
      <FlatList
        data={turns}
        keyExtractor={item => item.id}
        contentContainerStyle={styles.list}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={load} />}
        ListEmptyComponent={<Text style={styles.empty}>No conversations yet.</Text>}
        renderItem={({item}) => (
          <View style={styles.turn}>
            <Text style={styles.timestamp}>
              {new Date(item.created_at).toLocaleString()} · {item.emotion_state}
            </Text>
            <Text style={styles.you}>You: {item.transcript}</Text>
            <Text style={styles.oreo}>Oreo: {item.response}</Text>
          </View>
        )}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {flex: 1, backgroundColor: '#0F0E17'},
  list: {padding: 16, gap: 12},
  empty: {color: '#A7A9BE', textAlign: 'center', marginTop: 48},
  turn: {backgroundColor: '#1F1D33', borderRadius: 14, padding: 14, marginBottom: 12},
  timestamp: {color: '#6C5CE7', fontSize: 12, marginBottom: 6, textTransform: 'uppercase'},
  you: {color: '#FFFFFE', fontSize: 15, marginBottom: 4},
  oreo: {color: '#A7A9BE', fontSize: 15},
});
