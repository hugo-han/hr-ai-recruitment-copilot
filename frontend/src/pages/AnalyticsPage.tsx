import { useState, useEffect } from "react";
import { Card, Typography, Statistic, Row, Col, Table, Tag, DatePicker, Space, message } from "antd";
import { getOverview, AnalyticsOverview } from "../api/analytics";

const { Title } = Typography;
const { RangePicker } = DatePicker;

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsOverview | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchData = async (start?: string, end?: string) => {
    setLoading(true);
    try {
      const result = await getOverview(start, end);
      setData(result);
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } catch (err: any) {
      message.error(err?.message || "加载数据失败");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const onRangeChange = (_: unknown, dateStrings: [string, string]) => {
    if (dateStrings[0] && dateStrings[1]) {
      fetchData(dateStrings[0], dateStrings[1]);
    }
  };

  const cr = data?.conversion_rate || {};
  const funnel = [
    { stage: "上传", count: cr.uploaded || 0, rate: 1 },
    { stage: "已评分", count: cr.analyzed || 0, rate: cr.analyzed_rate || 0 },
    { stage: "已面试", count: cr.interviewed || 0, rate: cr.interviewed_rate || 0 },
    { stage: "已评价", count: cr.evaluated || 0, rate: cr.evaluated_rate || 0 },
    { stage: "推荐", count: cr.recommended || 0, rate: cr.recommended_rate || 0 },
  ];

  const channelData = Object.entries(data?.channel_effectiveness || {}).map(([ch, val]) => ({
    channel: ch,
    uploaded: val.uploaded,
    recommended: val.recommended,
    rate: (val.recommended_rate * 100).toFixed(1) + "%",
  }));

  return (
    <div>
      <Title level={3}>招聘数据分析看板</Title>

      <Space style={{ marginBottom: 16 }}>
        <RangePicker onChange={onRangeChange} />
      </Space>

      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card loading={loading}>
            <Statistic title="岗位数" value={data?.total_jobs || 0} />
          </Card>
        </Col>
        <Col span={6}>
          <Card loading={loading}>
            <Statistic title="简历数" value={data?.total_resumes || 0} />
          </Card>
        </Col>
        <Col span={6}>
          <Card loading={loading}>
            <Statistic title="面试数" value={data?.total_interviews || 0} />
          </Card>
        </Col>
        <Col span={6}>
          <Card loading={loading}>
            <Statistic
              title="招聘周期（天）"
              value={data?.recruitment_cycle_days ?? "-"}
            />
          </Card>
        </Col>
      </Row>

      <Card title="漏斗转化率" loading={loading} style={{ marginBottom: 16 }}>
        <div style={{ display: "flex", alignItems: "flex-end", gap: 24, height: 200, padding: "24px 0" }}>
          {funnel.map((f) => {
            const h = Math.max(f.count > 0 ? 40 : 10, f.rate * 160);
            return (
              <div key={f.stage} style={{ flex: 1, textAlign: "center" }}>
                <div style={{ marginBottom: 4, fontWeight: 500 }}>{f.count}</div>
                <div
                  style={{
                    height: h,
                    background: `hsl(${210 - funnel.indexOf(f) * 30}, 70%, 55%)`,
                    borderRadius: "4px 4px 0 0",
                    minWidth: 60,
                    transition: "height 0.3s",
                  }}
                />
                <div style={{ marginTop: 8, fontSize: 12, color: "#888" }}>
                  {f.stage}
                  <br />
                  {(f.rate * 100).toFixed(1)}%
                </div>
              </div>
            );
          })}
        </div>
      </Card>

      <Card title="渠道效果" loading={loading}>
        {channelData.length > 0 ? (
          <Table
            rowKey="channel"
            columns={[
              { title: "渠道", dataIndex: "channel", render: (c: string) => <Tag color="geekblue">{c}</Tag> },
              { title: "上传", dataIndex: "uploaded" },
              { title: "推荐", dataIndex: "recommended" },
              { title: "推荐率", dataIndex: "rate" },
            ]}
            dataSource={channelData}
            pagination={false}
            size="small"
          />
        ) : (
          <Typography.Text type="secondary">暂无数据</Typography.Text>
        )}
      </Card>
    </div>
  );
}
